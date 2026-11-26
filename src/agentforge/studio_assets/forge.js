"use strict";

// The centerpiece is a live perspective rendering of three beveled 3D meshes.
(() => {
  const canvas = document.getElementById("forge-canvas");
  const toggle = document.getElementById("motion-button");
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    toggle.hidden = true;
    return;
  }

  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const tau = Math.PI * 2;
  const light = [-0.46, -0.56, 0.69];
  const bands = [
    { radius: 1.04, width: .225, depth: .24, tilt: [.33, -.32, .12], color: [176, 119, 74], edge: [101, 60, 40], pace: .44 },
    { radius: .805, width: .19, depth: .235, tilt: [1.19, .72, -.48], color: [130, 153, 128], edge: [47, 73, 56], pace: -.42 },
    { radius: .548, width: .145, depth: .20, tilt: [-.68, 1.02, .82], color: [201, 154, 107], edge: [117, 80, 54], pace: .85 },
  ];
  const segments = 72;
  let width = 0;
  let height = 0;
  let phase = 0;
  let yaw = 0;
  let pitch = 0;
  let drag = null;
  let animated = !reducedMotion.matches;
  let frame = 0;
  let lastTime = 0;

  function mesh({ radius, width, depth }) {
    const r0 = radius - width / 2;
    const r1 = radius + width / 2;
    const z = depth / 2;
    const bevel = .034;
    const profile = [
      [r0 + bevel, z], [r1 - bevel, z], [r1, z - bevel], [r1, -z + bevel],
      [r1 - bevel, -z], [r0 + bevel, -z], [r0, -z + bevel], [r0, z - bevel],
    ];
    return Array.from({ length: segments }, (_, segment) => {
      const angle = segment * tau / segments;
      return profile.map(([r, level]) => [r * Math.cos(angle), r * Math.sin(angle), level]);
    });
  }

  for (const band of bands) band.mesh = mesh(band);

  function rotation(x, y, z) {
    const sx = Math.sin(x), cx = Math.cos(x);
    const sy = Math.sin(y), cy = Math.cos(y);
    const sz = Math.sin(z), cz = Math.cos(z);
    return [
      [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
      [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
      [-sy, cy * sx, cy * cx],
    ];
  }

  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function transform(matrix, point) { return matrix.map((row) => dot(row, point)); }

  function normal(origin, tangent, edge) {
    const ax = tangent[0] - origin[0], ay = tangent[1] - origin[1], az = tangent[2] - origin[2];
    const bx = edge[0] - origin[0], by = edge[1] - origin[1], bz = edge[2] - origin[2];
    const x = ay * bz - az * by, y = az * bx - ax * bz, z = ax * by - ay * bx;
    const length = Math.hypot(x, y, z);
    return [x / length, y / length, z / length];
  }

  function collectFaces() {
    const faces = [];
    const global = rotation(-.17 + pitch, .25 + yaw, -.17);
    for (const band of bands) {
      const [x, y, z] = band.tilt;
      const angle = phase * band.pace;
      const turn = rotation(x + .39 * Math.sin(angle), y + .57 * Math.sin(angle + .15), z + angle * .66);
      const vertices = band.mesh.map((segment) => segment.map((point) => transform(global, transform(turn, point))));
      for (let i = 0; i < segments; i++) {
        const next = (i + 1) % segments;
        for (let side = 0; side < 8; side++) {
          const other = (side + 1) % 8;
          const points = [vertices[i][side], vertices[i][other], vertices[next][other], vertices[next][side]];
          const direction = normal(points[0], points[1], points[3]);
          const distance = points.reduce((total, point) => total + point[2], 0) / 4;
          const view = [-points[0][0] / 4.6, -points[0][1] / 4.6, 1];
          if (dot(direction, view) > -.025) faces.push({ points, direction, distance, band, side, index: i });
        }
      }
    }
    return faces.sort((a, b) => a.distance - b.distance);
  }

  function shade({ direction, distance, band, side, index }) {
    const diffuse = Math.max(0, dot(direction, light));
    const reflection = Math.max(0, dot(direction, [-.27, -.32, .907]));
    const glint = .30 * reflection ** 21 + .14 * Math.max(0, dot(direction, [.78, -.17, .60])) ** 24;
    const finish = .94 + .038 * Math.sin(index * 1.4) + .023 * Math.cos(index * 3.1);
    const rim = side % 2 === 1 ? 1.05 : .96;
    const intensity = (.30 + .67 * diffuse + .13 * Math.abs(direction[0]) + Math.max(distance, -.2) * .055) * finish * rim;
    const channels = band.color.map((value, idx) => Math.round(Math.min(255, value * intensity + band.edge[idx] * .19 + 255 * glint)));
    return `rgb(${channels.join(",")})`;
  }

  function drawOrbits(cx, cy, scale) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#cddec123";
    ctx.setLineDash([2, 5]);
    ctx.beginPath();
    ctx.ellipse(0, 0, scale * 1.65, scale * .96, -.37, 0, tau);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = "#d9e2ca18";
    ctx.beginPath();
    ctx.ellipse(0, 0, scale * 1.46, scale * 1.48, .24, 0, tau);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-scale * 1.62, 0);
    ctx.lineTo(scale * 1.62, 0);
    ctx.moveTo(0, -scale * 1.65);
    ctx.lineTo(0, scale * 1.65);
    ctx.stroke();

    const orbit = phase * .74 - .8;
    const satellites = [[Math.cos(orbit) * 1.53, Math.sin(orbit) * .81], [-1.34, -.58], [1.03, -.96], [1.32, .56]];
    for (const [x, y] of satellites) {
      ctx.beginPath();
      ctx.fillStyle = x > 0 ? "#deba93bf" : "#bbcbb3a8";
      ctx.arc(x * scale, y * scale, 2.1, 0, tau);
      ctx.fill();
    }
    ctx.restore();
  }

  function draw() {
    if (!width || !height) return;
    ctx.clearRect(0, 0, width, height);
    const scale = Math.min(width * .285, height * .35);
    const cx = width * .52;
    const cy = height * .5;
    const halo = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale * 1.9);
    halo.addColorStop(0, "#9baa7e2e");
    halo.addColorStop(1, "#9baa7e00");
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, width, height);

    ctx.save();
    ctx.translate(cx, cy + scale * 1.05);
    ctx.scale(1, .23);
    const shadow = ctx.createRadialGradient(0, 0, 0, 0, 0, scale * 1.48);
    shadow.addColorStop(0, "#111d16bd");
    shadow.addColorStop(1, "#111d1600");
    ctx.fillStyle = shadow;
    ctx.fillRect(-scale * 1.5, -scale * 1.5, scale * 3, scale * 3);
    ctx.restore();
    drawOrbits(cx, cy, scale);

    ctx.lineWidth = .55;
    ctx.lineJoin = "round";
    for (const face of collectFaces()) {
      ctx.beginPath();
      face.points.forEach(([x, y, z], index) => {
        const perspective = 4.6 / (4.6 - z);
        const X = cx + x * scale * perspective;
        const Y = cy + y * scale * perspective;
        if (index === 0) ctx.moveTo(X, Y);
        else ctx.lineTo(X, Y);
      });
      const color = shade(face);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      ctx.fill();
      ctx.stroke();
    }
  }

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function tick(now) {
    if (now - lastTime >= 32) {
      phase += lastTime ? Math.min(.05, (now - lastTime) / 1000) : 0;
      lastTime = now;
      draw();
    }
    frame = requestAnimationFrame(tick);
  }

  function setMotion(on) {
    animated = on;
    toggle.textContent = on ? "Pause motion" : "Play motion";
    toggle.setAttribute("aria-pressed", String(!on));
    cancelAnimationFrame(frame);
    lastTime = 0;
    if (on) frame = requestAnimationFrame(tick);
  }

  canvas.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    drag = { x: event.clientX, y: event.clientY, yaw, pitch };
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!drag) return;
    yaw = drag.yaw + (event.clientX - drag.x) * .012;
    pitch = drag.pitch + (event.clientY - drag.y) * .011;
    if (!animated) draw();
  });
  canvas.addEventListener("lostpointercapture", () => { drag = null; });
  toggle.addEventListener("click", () => setMotion(!animated));
  reducedMotion.addEventListener("change", (event) => setMotion(!event.matches));
  new ResizeObserver(resize).observe(canvas);
  resize();
  setMotion(animated);
})();
