// build.js
import { build } from 'esbuild';

import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Server (Neptune/DMZ) library bundle (ESM)
 * - Produces dist/r-file-viewer.bundle.js exporting buildRfvRouter(...)
 * - Designed to be imported and mounted inside Neptune's index.js
 */
await build({
  entryPoints: ['src/rfv-router.js'],
  outfile: 'dist/r-file-viewer.bundle.js',
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: ['node20'],
  sourcemap: true,
  legalComments: 'none',
  // Provide a require() that works under ESM if any non-external require remains.
  banner: {
    js: "import { createRequire as __createRequire } from 'module'; const require = __createRequire(import.meta.url);"
  },
  // <-- prevent bundling of express and node built-ins
  external: [
    // Runtime libs (CJS)
    'express',
    'mysql2',
    'sql-escaper',
    'safer-buffer',
    'depd',
    'cardinal',

    // Node built-ins (both plain and node:* specifiers)
    'path', 'fs', 'fs/promises', 'buffer', 'string_decoder', 'stream',
    'crypto', 'process', 'events', 'timers', 'tls', 'util', 'zlib', 'url', 'net',
    'node:path', 'node:fs', 'node:fs/promises', 'node:buffer', 'node:string_decoder',
    'node:stream', 'node:crypto', 'node:process', 'node:events', 'node:timers',
    'node:tls', 'node:util', 'node:zlib', 'node:url', 'node:net'
  ],
  define: {
    /* no override — allow runtime environment to be read normally
    'process.env.DEV_ENV_MODE': JSON.stringify(process.env.DEV_ENV_MODE ?? '0'),
    'process.env.DB_HOST': JSON.stringify(process.env.DB_HOST ?? 'localhost'),
    'process.env.DB_PORT': JSON.stringify(process.env.DB_PORT ?? '3307'),
    'process.env.DB_USER': JSON.stringify(process.env.DB_USER ?? 'dev'),
    'process.env.DB_PASS': JSON.stringify(process.env.DB_PASS ?? 'WWdev9876!'),
    'process.env.DB_NAME': JSON.stringify(process.env.DB_NAME ?? 'edgardb'),
    'process.env.S3_BUCKET': JSON.stringify(process.env.S3_BUCKET ?? 'archives.sec.gov'),
    'process.env.MYSQL_STUB_FILE': JSON.stringify(process.env.MYSQL_STUB_FILE ?? '/xbrldata/team_sun_stars/test/viewer/MySql_stub.json'),
    'process.env.DEBUG_LOG_FILE': JSON.stringify(process.env.DEBUG_LOG_FILE ?? '/xbrldata/team_sun_stars/test/viewer/viewerLog.txt'),
    'process.env.BUILD_TARGET': JSON.stringify('server'),
    */
  },
  absWorkingDir: __dirname,
  nodePaths: [path.join(__dirname, 'node_modules')],
});
console.log('Built dist/r-file-viewer.bundle.js');

/**
 * Transform-only bundle (IIFE, Node-free)
 * - Exposes global RFileViewer.transform (Arelle/PythonMonkey)
 * - No Node/Express/DB dependencies
 */
await build({
  entryPoints: ['src/transform.js'],
  outfile: 'dist/r-file-viewer.transform.iife.js',
  bundle: true,
  platform: 'neutral',
  format: 'iife',
  globalName: 'RFileViewer',
  target: ['es2020'],
  sourcemap: false,
  legalComments: 'none',
  mainFields: ['module', 'main'],
  define: {
    'process.env.BUILD_TARGET': JSON.stringify('transform'),
  },
  absWorkingDir: __dirname,
  nodePaths: [path.join(__dirname, 'node_modules')],
  // minify: true, // optional
});
console.log('Built dist/r-file-viewer.transform.iife.js');