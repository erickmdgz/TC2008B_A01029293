/**
 * Transformaciones 2D - Tarea CG_1
 * Autor: Erick Alonso Morales Dieguez - A01029293
 */

import * as twgl from 'twgl.js';
import GUI from 'lil-gui';
import { M2D } from './transformaciones2D.js';

// Shaders
const vertexShaderSource = `#version 300 es
in vec2 a_position;
in vec4 a_color;

uniform vec2 u_resolution;
uniform mat3 u_matrix;

out vec4 v_color;

void main() {
  // Aplicar matriz de transformación
  vec2 transformedPos = (u_matrix * vec3(a_position, 1.0)).xy;

  // Convertir de píxeles a clip space
  vec2 clipSpace = (transformedPos / u_resolution) * 2.0 - 1.0;

  gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
  v_color = a_color;
}
`;

const fragmentShaderSource = `#version 300 es
precision highp float;

in vec4 v_color;
out vec4 outColor;

void main() {
  outColor = v_color;
}
`;

/**
 * Crea la geometría de la cara (con ojos y boca)
 */
function createFaceArrays() {
  const positions = [];
  const colors = [];
  const indices = [];
  let indexOffset = 0;

  // Color de la piel (amarillo claro)
  const skinColor = [1.0, 0.9, 0.5, 1.0];

  // Crear cara circular usando triángulos (centro en origen)
  const faceRadius = 100;
  const faceSegments = 20;
  const centerX = 0;
  const centerY = 0;

  // Vértice central
  positions.push(centerX, centerY);
  colors.push(...skinColor);

  // Vértices del perímetro
  for (let i = 0; i <= faceSegments; i++) {
    const angle = (i / faceSegments) * Math.PI * 2;
    const x = centerX + Math.cos(angle) * faceRadius;
    const y = centerY + Math.sin(angle) * faceRadius;
    positions.push(x, y);
    colors.push(...skinColor);
  }

  // Índices para la cara
  for (let i = 0; i < faceSegments; i++) {
    indices.push(indexOffset, indexOffset + i + 1, indexOffset + i + 2);
  }

  indexOffset += faceSegments + 2;

  // Ojo izquierdo (triángulos formando un círculo pequeño)
  const eyeColor = [0.1, 0.1, 0.1, 1.0]; // Negro
  const leftEyeX = -30;
  const leftEyeY = -20;
  const eyeRadius = 10;
  const eyeSegments = 8;

  // Centro del ojo izquierdo
  positions.push(leftEyeX, leftEyeY);
  colors.push(...eyeColor);

  for (let i = 0; i <= eyeSegments; i++) {
    const angle = (i / eyeSegments) * Math.PI * 2;
    const x = leftEyeX + Math.cos(angle) * eyeRadius;
    const y = leftEyeY + Math.sin(angle) * eyeRadius;
    positions.push(x, y);
    colors.push(...eyeColor);
  }

  for (let i = 0; i < eyeSegments; i++) {
    indices.push(indexOffset, indexOffset + i + 1, indexOffset + i + 2);
  }

  indexOffset += eyeSegments + 2;

  // Ojo derecho
  const rightEyeX = 30;
  const rightEyeY = -20;

  positions.push(rightEyeX, rightEyeY);
  colors.push(...eyeColor);

  for (let i = 0; i <= eyeSegments; i++) {
    const angle = (i / eyeSegments) * Math.PI * 2;
    const x = rightEyeX + Math.cos(angle) * eyeRadius;
    const y = rightEyeY + Math.sin(angle) * eyeRadius;
    positions.push(x, y);
    colors.push(...eyeColor);
  }

  for (let i = 0; i < eyeSegments; i++) {
    indices.push(indexOffset, indexOffset + i + 1, indexOffset + i + 2);
  }

  indexOffset += eyeSegments + 2;

  // Boca (sonrisa usando triángulos)
  const mouthColor = [0.8, 0.2, 0.2, 1.0]; // Rojo
  const mouthY = 30;
  const mouthSegments = 10;
  const mouthWidth = 60;
  const mouthHeight = 20;

  // Centro de la boca
  positions.push(0, mouthY);
  colors.push(...mouthColor);

  // Vértices de la sonrisa (semicírculo)
  for (let i = 0; i <= mouthSegments; i++) {
    const t = i / mouthSegments;
    const angle = Math.PI * t; // De 0 a PI (semicírculo inferior)
    const x = Math.cos(angle) * mouthWidth;
    const y = mouthY + Math.sin(angle) * mouthHeight;
    positions.push(x, y);
    colors.push(...mouthColor);
  }

  for (let i = 0; i < mouthSegments; i++) {
    indices.push(indexOffset, indexOffset + i + 1, indexOffset + i + 2);
  }

  return {
    a_position: { numComponents: 2, data: new Float32Array(positions) },
    a_color: { numComponents: 4, data: new Float32Array(colors) },
    indices: { numComponents: 3, data: new Uint16Array(indices) }
  };
}

/**
 * Crea la geometría del pivote (cuadrado pequeño)
 */
function createPivotArrays() {
  const size = 10;
  const positions = [
    -size, -size,
     size, -size,
     size,  size,
    -size,  size
  ];

  // Color rojo brillante para el pivote
  const pivotColor = [1.0, 0.0, 0.0, 1.0];
  const colors = [
    ...pivotColor,
    ...pivotColor,
    ...pivotColor,
    ...pivotColor
  ];

  const indices = [
    0, 1, 2,
    0, 2, 3
  ];

  return {
    a_position: { numComponents: 2, data: new Float32Array(positions) },
    a_color: { numComponents: 4, data: new Float32Array(colors) },
    indices: { numComponents: 3, data: new Uint16Array(indices) }
  };
}

/**
 * Función principal
 */
function main() {
  const canvas = document.querySelector('#canvas');
  const gl = canvas.getContext('webgl2');

  if (!gl) {
    alert('WebGL 2 no está disponible');
    return;
  }

  // Crear programa de shaders
  const programInfo = twgl.createProgramInfo(gl, [vertexShaderSource, fragmentShaderSource]);

  // Crear objetos
  const objects = {
    face: {
      arrays: createFaceArrays(),
      bufferInfo: null,
      vao: null,
      transforms: {
        tx: 400,
        ty: 300,
        rotDeg: 0,
        sx: 1.0,
        sy: 1.0
      }
    },
    pivot: {
      arrays: createPivotArrays(),
      bufferInfo: null,
      vao: null,
      transforms: {
        px: 400,
        py: 300
      }
    }
  };

  // Crear buffers y VAOs
  objects.face.bufferInfo = twgl.createBufferInfoFromArrays(gl, objects.face.arrays);
  objects.face.vao = twgl.createVAOFromBufferInfo(gl, programInfo, objects.face.bufferInfo);

  objects.pivot.bufferInfo = twgl.createBufferInfoFromArrays(gl, objects.pivot.arrays);
  objects.pivot.vao = twgl.createVAOFromBufferInfo(gl, programInfo, objects.pivot.bufferInfo);

  // Configurar GUI
  const gui = new GUI();

  const pivotFolder = gui.addFolder('Pivote');
  pivotFolder.add(objects.pivot.transforms, 'px', 0, 800).name('Posición X');
  pivotFolder.add(objects.pivot.transforms, 'py', 0, 600).name('Posición Y');
  pivotFolder.open();

  const faceFolder = gui.addFolder('Cara');
  faceFolder.add(objects.face.transforms, 'tx', 0, 800).name('Traslación X');
  faceFolder.add(objects.face.transforms, 'ty', 0, 600).name('Traslación Y');
  faceFolder.add(objects.face.transforms, 'rotDeg', 0, 360).name('Rotación (°)');
  faceFolder.add(objects.face.transforms, 'sx', 0.1, 5.0).name('Escala X');
  faceFolder.add(objects.face.transforms, 'sy', 0.1, 5.0).name('Escala Y');
  faceFolder.open();

  /**
   * Dibuja la escena
   */
  function drawScene() {
    // Ajustar tamaño del canvas
    twgl.resizeCanvasToDisplaySize(canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Limpiar canvas
    gl.clearColor(0.95, 0.95, 0.95, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    // Usar programa
    gl.useProgram(programInfo.program);

    // Dibujar pivote
    const pivotMatrix = M2D.translation(
      objects.pivot.transforms.px,
      objects.pivot.transforms.py
    );

    gl.bindVertexArray(objects.pivot.vao);
    twgl.setUniforms(programInfo, {
      u_resolution: [gl.canvas.width, gl.canvas.height],
      u_matrix: pivotMatrix
    });
    twgl.drawBufferInfo(gl, objects.pivot.bufferInfo);

    // Dibujar cara con transformaciones compuestas
    // M_cara = T(tx, ty) · T(px, py) · R(rot) · T(−px, −py) · S(sx, sy)
    const { tx, ty, rotDeg, sx, sy } = objects.face.transforms;
    const { px, py } = objects.pivot.transforms;
    const rotRadians = (rotDeg * Math.PI) / 180;

    const faceMatrix = M2D.composite([
      M2D.translation(tx, ty),
      M2D.translation(px, py),
      M2D.rotation(rotRadians),
      M2D.translation(-px, -py),
      M2D.scale(sx, sy)
    ]);

    gl.bindVertexArray(objects.face.vao);
    twgl.setUniforms(programInfo, {
      u_resolution: [gl.canvas.width, gl.canvas.height],
      u_matrix: faceMatrix
    });
    twgl.drawBufferInfo(gl, objects.face.bufferInfo);

    // Siguiente frame
    requestAnimationFrame(drawScene);
  }

  // Iniciar loop de renderizado
  drawScene();
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', main);
} else {
  main();
}
