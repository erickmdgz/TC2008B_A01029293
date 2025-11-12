/**
 * Biblioteca de matrices 2D (3x3) para transformaciones homogéneas
 * Formato: column-major (columnas consecutivas en memoria)
 * Autor: Erick Alonso Morales Dieguez - A01029293
 */

export class M2D {
  /**
   * Crea una matriz identidad 3x3
   * @returns {number[]} Matriz identidad
   */
  static identity() {
    return [
      1, 0, 0,
      0, 1, 0,
      0, 0, 1
    ];
  }

  /**
   * Crea una matriz de traslación
   * @param {number} tx - Traslación en x
   * @param {number} ty - Traslación en y
   * @returns {number[]} Matriz de traslación
   */
  static translation(tx, ty) {
    return [
      1, 0, 0,
      0, 1, 0,
      tx, ty, 1
    ];
  }

  /**
   * Crea una matriz de rotación
   * @param {number} angleRadians - Ángulo de rotación en radianes
   * @returns {number[]} Matriz de rotación
   */
  static rotation(angleRadians) {
    const c = Math.cos(angleRadians);
    const s = Math.sin(angleRadians);
    return [
      c, s, 0,
      -s, c, 0,
      0, 0, 1
    ];
  }

  /**
   * Crea una matriz de escala
   * @param {number} sx - Factor de escala en x
   * @param {number} sy - Factor de escala en y
   * @returns {number[]} Matriz de escala
   */
  static scale(sx, sy) {
    return [
      sx, 0, 0,
      0, sy, 0,
      0, 0, 1
    ];
  }

  /**
   * Multiplica dos matrices 3x3 (column-major)
   * @param {number[]} ma - Primera matriz
   * @param {number[]} mb - Segunda matriz
   * @returns {number[]} Resultado de ma * mb
   */
  static multiply(ma, mb) {
    const result = [];

    // Multiplicación de matrices 3x3 en column-major
    // result[col * 3 + row] = sum(ma[k * 3 + row] * mb[col * 3 + k]) for k=0..2
    for (let col = 0; col < 3; col++) {
      for (let row = 0; row < 3; row++) {
        let sum = 0;
        for (let k = 0; k < 3; k++) {
          sum += ma[k * 3 + row] * mb[col * 3 + k];
        }
        result[col * 3 + row] = sum;
      }
    }

    return result;
  }

  /**
   * Aplica múltiples transformaciones en orden (helper)
   * @param {number[][]} transforms - Array de matrices a multiplicar
   * @returns {number[]} Matriz compuesta resultante
   */
  static composite(transforms) {
    if (transforms.length === 0) {
      return M2D.identity();
    }

    let result = transforms[0];
    for (let i = 1; i < transforms.length; i++) {
      result = M2D.multiply(result, transforms[i]);
    }

    return result;
  }
}
