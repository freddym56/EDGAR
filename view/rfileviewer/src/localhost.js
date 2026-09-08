// Edgar(tm) r-file-viewer was created by staff of the U.S. Securities and Exchange Commission.
// Data and content created by government employees within the scope of their employment
// are not subject to domestic copyright protection. 17 U.S.C. 105.

// src/localhost.js
import { server } from './server.js';

// Allow CLI launch: node dist/viewer.bundle.cjs --mode=server
if (typeof process !== 'undefined') { // } && process.argv.includes('--mode=server')) {
  server();
}

// Re-export server to allow programmatic use
export { server };
