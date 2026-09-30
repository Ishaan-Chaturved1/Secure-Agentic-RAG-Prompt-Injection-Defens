import React, { useEffect, useRef } from 'react';

export default function CyberWaveCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = canvas.parentElement.offsetWidth);
    let height = (canvas.height = canvas.parentElement.offsetHeight);

    // Mouse coordinates with smooth interpolation
    const mouse = {
      x: width * 0.65,
      y: height * 0.45,
      targetX: width * 0.65,
      targetY: height * 0.45,
      isHovered: false,
    };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.targetX = e.clientX - rect.left;
      mouse.targetY = e.clientY - rect.top;
      mouse.isHovered = true;
    };

    const handleMouseLeave = () => {
      mouse.isHovered = false;
      mouse.targetX = width * 0.65;
      mouse.targetY = height * 0.45;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    const handleResize = () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.offsetWidth;
      height = canvas.height = canvas.parentElement.offsetHeight;
    };

    window.addEventListener('resize', handleResize);

    // Wave parameters
    const waveCount = 18;
    let time = 0;

    const render = () => {
      time += 0.012;

      // Smooth mouse interpolation (spring-like inertia)
      mouse.x += (mouse.targetX - mouse.x) * 0.06;
      mouse.y += (mouse.targetY - mouse.y) * 0.06;

      ctx.clearRect(0, 0, width, height);

      // Draw subtle cyan ambient glow centered at mouse
      const glowGrad = ctx.createRadialGradient(
        mouse.x,
        mouse.y,
        10,
        mouse.x,
        mouse.y,
        width > 800 ? 380 : 220
      );
      glowGrad.addColorStop(0, 'rgba(6, 182, 212, 0.12)');
      glowGrad.addColorStop(0.5, 'rgba(14, 165, 233, 0.04)');
      glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = glowGrad;
      ctx.fillRect(0, 0, width, height);

      // Draw cybernetic wave lines
      for (let i = 0; i < waveCount; i++) {
        ctx.beginPath();

        const progress = i / waveCount;
        const baseY = height * 0.28 + i * (height * 0.038);
        const freq = 0.0022 + i * 0.00015;
        const speed = time * (0.8 + i * 0.04);
        const baseAmp = 35 + i * 3.5;

        // Gradient color for each line: cyan to electric sky blue
        const lineGrad = ctx.createLinearGradient(0, 0, width, 0);
        const opacity = Math.sin(progress * Math.PI) * 0.45 + 0.12;
        lineGrad.addColorStop(0, `rgba(8, 145, 178, ${opacity * 0.2})`);
        lineGrad.addColorStop(0.35, `rgba(6, 182, 212, ${opacity * 0.9})`);
        lineGrad.addColorStop(0.7, `rgba(34, 211, 238, ${opacity * 0.75})`);
        lineGrad.addColorStop(1, `rgba(14, 165, 233, ${opacity * 0.25})`);

        ctx.strokeStyle = lineGrad;
        ctx.lineWidth = i % 3 === 0 ? 1.6 : 0.85;

        if (i % 4 === 1) {
          ctx.setLineDash([4, 6]);
        } else {
          ctx.setLineDash([]);
        }

        const step = 8;
        for (let x = -50; x <= width + 50; x += step) {
          // Autonomous sine wave
          const naturalWave = Math.sin(x * freq + speed) * baseAmp + 
                              Math.cos(x * freq * 0.5 - speed * 0.7) * (baseAmp * 0.4);

          // Distance to interactive mouse cursor
          const dx = x - mouse.x;
          const dy = (baseY + naturalWave) - mouse.y;
          const dist = Math.hypot(dx, dy);

          // Dynamic interactive cursor warping effect
          const influenceRadius = 260;
          let mouseDeform = 0;

          if (dist < influenceRadius) {
            const factor = 1 - dist / influenceRadius;
            // Smooth bell curve with harmonic ripples
            mouseDeform = Math.sin(factor * Math.PI) * 65 * (1 - progress * 0.3);
            // Add a directional push away from cursor
            if (dy < 0) mouseDeform = -mouseDeform;
          }

          const y = baseY + naturalWave + mouseDeform;

          if (x === -50) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        ctx.stroke();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none select-none z-0"
    />
  );
}
