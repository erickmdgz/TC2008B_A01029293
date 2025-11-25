/*
Activity CG_2: 3D Building Model Generator (Truncated Cone)

Description: This program generates a 3D OBJ file representing a building
with a truncated cone shape. It accepts command line parameters to customize
the number of sides, height, bottom radius, and top radius. The output includes
vertices, normals, and triangulated faces for proper 3D rendering.

Author: Erick Alonso Morales Dieguez
Matricula: A01029293
Date: 24/11/2025
*/

'use strict';

const fileSystem = require('fs');

// Default configuration values
const DEFAULT_SIDES = 8;
const DEFAULT_HEIGHT = 6.0;
const DEFAULT_BOTTOM_RADIUS = 1.0;
const DEFAULT_TOP_RADIUS = 0.8;

// Validation boundaries
const MIN_POLYGON_SIDES = 3;
const MAX_POLYGON_SIDES = 36;


/*
Function: extractCommandLineArgs
Purpose: Reads and parses command line arguments into a configuration object
Parameters: None (reads from process.argv)
Returns: Object containing sides, height, bottomRadius, topRadius, and outputFile
*/
function extractCommandLineArgs() {
    const rawArgs = process.argv.slice(2);

    let polygonSides = DEFAULT_SIDES;
    let buildingHeight = DEFAULT_HEIGHT;
    let baseRadius = DEFAULT_BOTTOM_RADIUS;
    let topRadius = DEFAULT_TOP_RADIUS;

    if (rawArgs[0] !== undefined) {
        polygonSides = parseInt(rawArgs[0], 10);
    }
    if (rawArgs[1] !== undefined) {
        buildingHeight = parseFloat(rawArgs[1]);
    }
    if (rawArgs[2] !== undefined) {
        baseRadius = parseFloat(rawArgs[2]);
    }
    if (rawArgs[3] !== undefined) {
        topRadius = parseFloat(rawArgs[3]);
    }

    polygonSides = enforceValidation(polygonSides, buildingHeight, baseRadius, topRadius);

    const outputFile = `building_${polygonSides}_${buildingHeight}_${baseRadius}_${topRadius}.obj`;

    return {
        sides: polygonSides,
        height: buildingHeight,
        bottomRadius: baseRadius,
        topRadius: topRadius,
        outputFile: outputFile
    };
}


/*
Function: enforceValidation
Purpose: Validates and adjusts input parameters to ensure they fall within acceptable ranges
Parameters:
    - sides: Number of polygon sides
    - height: Building height
    - radiusBottom: Bottom radius value
    - radiusTop: Top radius value
Returns: Validated number of sides (other validations exit on failure)
*/
function enforceValidation(sides, height, radiusBottom, radiusTop) {
    let validatedSides = sides;

    if (Number.isNaN(validatedSides) || validatedSides < MIN_POLYGON_SIDES) {
        validatedSides = MIN_POLYGON_SIDES;
        console.warn(`Warning: sides adjusted to minimum value ${MIN_POLYGON_SIDES}`);
    } else if (validatedSides > MAX_POLYGON_SIDES) {
        validatedSides = MAX_POLYGON_SIDES;
        console.warn(`Warning: sides adjusted to maximum value ${MAX_POLYGON_SIDES}`);
    }

    if (Number.isNaN(height) || height <= 0) {
        console.error('Error: height must be a positive number');
        process.exit(1);
    }

    if (Number.isNaN(radiusBottom) || radiusBottom <= 0) {
        console.error('Error: bottom radius must be a positive number');
        process.exit(1);
    }

    if (Number.isNaN(radiusTop) || radiusTop <= 0) {
        console.error('Error: top radius must be a positive number');
        process.exit(1);
    }

    return validatedSides;
}


/*
Function: createRadiusProfile
Purpose: Generates an array of radius values along the height of the building,
         including sinusoidal variation for visual interest
Parameters:
    - config: Configuration object with height, bottomRadius, topRadius
Returns: Array of radius values for each horizontal slice
*/
function createRadiusProfile(config) {
    const baseRad = config.bottomRadius;
    const topRad = config.topRadius;
    const totalHeight = config.height;

    // Calculate number of horizontal slices based on height
    const sliceCount = Math.min(8, Math.max(3, Math.floor(totalHeight / 2)));

    const radiusValues = [];
    let idx = 0;

    while (idx < sliceCount) {
        const interpolationFactor = idx / (sliceCount - 1);
        let currentRadius = 0;

        if (idx === 0) {
            currentRadius = baseRad;
        } else if (idx === sliceCount - 1) {
            currentRadius = topRad;
        } else {
            // Linear interpolation between base and top
            const linearRadius = baseRad + (topRad - baseRad) * interpolationFactor;

            // Add sinusoidal bulge for aesthetic variation
            const bulgeAmount = 0.3;
            const maxRadius = baseRad > topRad ? baseRad : topRad;
            const sinVariation = Math.sin(Math.PI * interpolationFactor) * bulgeAmount * maxRadius;

            currentRadius = linearRadius + sinVariation;
        }

        radiusValues.push(currentRadius);
        idx = idx + 1;
    }

    return radiusValues;
}


/*
Function: computeVertexRings
Purpose: Generates all vertices for the building by creating rings of points
         at each height level defined by the radius profile
Parameters:
    - config: Configuration object with sides and height
    - radiusProfile: Array of radius values for each level
Returns: Array of vertex objects with x, y, z coordinates
*/
function computeVertexRings(config, radiusProfile) {
    const vertexList = [];
    const totalRings = radiusProfile.length;
    const sideCount = config.sides;
    const fullHeight = config.height;

    for (let ringIndex = 0; ringIndex < totalRings; ringIndex = ringIndex + 1) {
        const yPosition = (ringIndex / (totalRings - 1)) * fullHeight;
        const ringRadius = radiusProfile[ringIndex];

        for (let vertexIndex = 0; vertexIndex < sideCount; vertexIndex = vertexIndex + 1) {
            const theta = (vertexIndex / sideCount) * 2.0 * Math.PI;

            const xCoord = ringRadius * Math.cos(theta);
            const zCoord = ringRadius * Math.sin(theta);

            vertexList.push({
                x: xCoord,
                y: yPosition,
                z: zCoord
            });
        }
    }

    return vertexList;
}


/*
Function: calculateSurfaceNormals
Purpose: Computes normal vectors for each sector of the lateral surface
         using parametric surface derivatives and cross product
Parameters:
    - sideCount: Number of sides in the polygon
    - lowerRadius: Radius at lower level
    - upperRadius: Radius at upper level
    - segmentHeight: Height of this segment
Returns: Array of normal vectors with x, y, z components
*/
function calculateSurfaceNormals(sideCount, lowerRadius, upperRadius, segmentHeight) {
    const normalVectors = [];
    const angularStep = (2.0 * Math.PI) / sideCount;

    const averageRadius = (lowerRadius + upperRadius) / 2.0;
    const radialDerivative = (upperRadius - lowerRadius) / segmentHeight;

    let sectorIndex = 0;
    while (sectorIndex < sideCount) {
        // Use center angle of the sector
        const centerAngle = (sectorIndex + 0.5) * angularStep;

        // Tangent vector in theta direction
        const tangentThetaX = -averageRadius * Math.sin(centerAngle);
        const tangentThetaY = 0.0;
        const tangentThetaZ = averageRadius * Math.cos(centerAngle);

        // Tangent vector in y direction
        const tangentYX = radialDerivative * Math.cos(centerAngle);
        const tangentYY = 1.0;
        const tangentYZ = radialDerivative * Math.sin(centerAngle);

        // Cross product to get normal
        let normalX = tangentThetaY * tangentYZ - tangentThetaZ * tangentYY;
        let normalY = tangentThetaZ * tangentYX - tangentThetaX * tangentYZ;
        let normalZ = tangentThetaX * tangentYY - tangentThetaY * tangentYX;

        // Normalize the vector
        const magnitude = Math.sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ);
        normalX = normalX / magnitude;
        normalY = normalY / magnitude;
        normalZ = normalZ / magnitude;

        // Ensure upward-facing component is positive
        if (normalY < 0) {
            normalX = -normalX;
            normalY = -normalY;
            normalZ = -normalZ;
        }

        normalVectors.push({
            x: normalX,
            y: normalY,
            z: normalZ
        });

        sectorIndex = sectorIndex + 1;
    }

    return normalVectors;
}


/*
Function: formatDecimal
Purpose: Formats a number to 4 decimal places for OBJ file output
Parameters:
    - value: Numeric value to format
Returns: String representation with 4 decimal places
*/
function formatDecimal(value) {
    return value.toFixed(4);
}


/*
Function: assembleObjFile
Purpose: Constructs the complete OBJ file content including header, vertices,
         normals, and faces for the building geometry
Parameters:
    - config: Configuration object with all building parameters
    - vertices: Array of vertex positions
    - radiusProfile: Array of radius values per level
Returns: String containing the complete OBJ file content
*/
function assembleObjFile(config, vertices, radiusProfile) {
    const sideCount = config.sides;
    const buildingHeight = config.height;
    const ringCount = radiusProfile.length;

    // Calculate totals for header
    const vertexTotal = 2 + sideCount * ringCount;
    const normalTotal = 2 + sideCount * (ringCount - 1) * 2;
    const faceTotal = sideCount * 2 + sideCount * (ringCount - 1) * 2;

    let fileContent = '';

    // Write header comments
    fileContent = fileContent + `# OBJ file ${config.outputFile}\n`;
    fileContent = fileContent + `# ${vertexTotal} vertices\n`;
    fileContent = fileContent + `# ${normalTotal} normals\n`;
    fileContent = fileContent + `# ${faceTotal} faces\n`;

    // Write bottom center vertex
    fileContent = fileContent + `v ${formatDecimal(0.0)} ${formatDecimal(0.0)} ${formatDecimal(0.0)}\n`;

    // Write ring vertices
    let vertexIdx = 0;
    while (vertexIdx < vertices.length) {
        const vtx = vertices[vertexIdx];
        fileContent = fileContent + `v ${formatDecimal(vtx.x)} ${formatDecimal(vtx.y)} ${formatDecimal(vtx.z)}\n`;
        vertexIdx = vertexIdx + 1;
    }

    // Write top center vertex
    fileContent = fileContent + `v ${formatDecimal(0.0)} ${formatDecimal(buildingHeight)} ${formatDecimal(0.0)}\n`;

    // Write cap normals
    fileContent = fileContent + `vn ${formatDecimal(0.0)} ${formatDecimal(-1.0)} ${formatDecimal(0.0)}\n`;
    fileContent = fileContent + `vn ${formatDecimal(0.0)} ${formatDecimal(1.0)} ${formatDecimal(0.0)}\n`;

    // Write lateral normals for each segment
    for (let segIdx = 0; segIdx < ringCount - 1; segIdx = segIdx + 1) {
        const rLower = radiusProfile[segIdx];
        const rUpper = radiusProfile[segIdx + 1];
        const segHeight = buildingHeight / (ringCount - 1);
        const segmentNormals = calculateSurfaceNormals(sideCount, rLower, rUpper, segHeight);

        for (let nIdx = 0; nIdx < sideCount; nIdx = nIdx + 1) {
            const nrm = segmentNormals[nIdx];
            // Write each normal twice (for both triangles of the quad)
            fileContent = fileContent + `vn ${formatDecimal(nrm.x)} ${formatDecimal(nrm.y)} ${formatDecimal(nrm.z)}\n`;
            fileContent = fileContent + `vn ${formatDecimal(nrm.x)} ${formatDecimal(nrm.y)} ${formatDecimal(nrm.z)}\n`;
        }
    }

    // Write bottom cap faces
    const bottomCenter = 1;
    for (let s = 0; s < sideCount; s = s + 1) {
        const nextS = (s + 1) % sideCount;
        const v0 = 2 + s;
        const v1 = 2 + nextS;
        fileContent = fileContent + `f ${v1}//1 ${bottomCenter}//1 ${v0}//1\n`;
    }

    // Write lateral faces
    for (let seg = 0; seg < ringCount - 1; seg = seg + 1) {
        for (let side = 0; side < sideCount; side = side + 1) {
            const nextSide = (side + 1) % sideCount;

            const baseRingOffset = 2 + seg * sideCount;
            const upperRingOffset = 2 + (seg + 1) * sideCount;

            const vertA = baseRingOffset + side;
            const vertB = baseRingOffset + nextSide;
            const vertC = upperRingOffset + nextSide;
            const vertD = upperRingOffset + side;

            const normalBase = 3 + seg * sideCount * 2 + side * 2;
            const normalIdx1 = normalBase;
            const normalIdx2 = normalBase + 1;

            // Lower triangle
            fileContent = fileContent + `f ${vertC}//${normalIdx1} ${vertB}//${normalIdx1} ${vertA}//${normalIdx1}\n`;
            // Upper triangle
            fileContent = fileContent + `f ${vertD}//${normalIdx2} ${vertC}//${normalIdx2} ${vertA}//${normalIdx2}\n`;
        }
    }

    // Write top cap faces
    const topCenter = vertexTotal;
    const topRingOffset = 2 + (ringCount - 1) * sideCount;
    for (let s = 0; s < sideCount; s = s + 1) {
        const nextS = (s + 1) % sideCount;
        const v0 = topRingOffset + s;
        const v1 = topRingOffset + nextS;
        fileContent = fileContent + `f ${v0}//2 ${topCenter}//2 ${v1}//2\n`;
    }

    return fileContent;
}


/*
Function: saveToFile
Purpose: Writes the generated OBJ content to disk
Parameters:
    - filename: Output file path
    - content: String content to write
Returns: None (exits on error)
*/
function saveToFile(filename, content) {
    try {
        fileSystem.writeFileSync(filename, content);
        console.log(`File generated: ${filename}`);
    } catch (err) {
        console.error(`Error writing file: ${err.message}`);
        process.exit(1);
    }
}


/*
Function: executeGenerator
Purpose: Main entry point that orchestrates the building generation process
Parameters: None
Returns: None
*/
function executeGenerator() {
    const buildingConfig = extractCommandLineArgs();

    console.log('Generating building with parameters:');
    console.log(`  Sides: ${buildingConfig.sides}`);
    console.log(`  Height: ${buildingConfig.height}`);
    console.log(`  Bottom radius: ${buildingConfig.bottomRadius}`);
    console.log(`  Top radius: ${buildingConfig.topRadius}`);

    const radiusProfile = createRadiusProfile(buildingConfig);
    console.log(`  Rings: ${radiusProfile.length}`);

    const vertexData = computeVertexRings(buildingConfig, radiusProfile);

    const ringCount = radiusProfile.length;
    const totalVertices = 2 + buildingConfig.sides * ringCount;
    const totalNormals = 2 + buildingConfig.sides * (ringCount - 1) * 2;
    const totalFaces = buildingConfig.sides * 2 + buildingConfig.sides * (ringCount - 1) * 2;

    console.log(`  Vertices: ${totalVertices}`);
    console.log(`  Normals: ${totalNormals}`);
    console.log(`  Faces: ${totalFaces}`);

    const objContent = assembleObjFile(buildingConfig, vertexData, radiusProfile);
    saveToFile(buildingConfig.outputFile, objContent);
}


// Start the program
executeGenerator();
