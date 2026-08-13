// copy-assets.js
import fs from 'fs';
import path from 'path';

const sourceDir = path.resolve('src/public');
const destDir = path.resolve('dist/public');

function copyRecursive(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

try {
  console.log(`Copying assets from ${sourceDir} to ${destDir}...`);
  copyRecursive(sourceDir, destDir);

  // Normalize the official SEC accordion script name at destination:
  const srcAccordionAlt = path.join(sourceDir, 'include', 'accordionMenu-fromSecWebsiteInclude.js');
  const destAccordionNorm = path.join(destDir, 'include', 'accordionMenu.js');
  if (fs.existsSync(srcAccordionAlt)) {
    fs.copyFileSync(srcAccordionAlt, destAccordionNorm);
    console.log('Normalized accordion script to /include/accordionMenu.js');
  }

  // Optional: verify jQuery is present
  const jqueryFile = path.join(destDir, 'include', 'jquery-3.7.1.min.js');
  if (!fs.existsSync(jqueryFile)) {
    console.warn('Warning: /include/jquery-3.7.1.min.js not found in dist. Place it under src/public/include/');
  }

  // Optional: verify our loader is present
  const loaderFile = path.join(destDir, 'include', 'sec-viewer.js');
  if (!fs.existsSync(loaderFile)) {
    console.warn('Warning: /include/sec-viewer.js not found in dist. Place it under src/public/include/');
  }

  console.log('Assets copied successfully.');
} catch (err) {
  console.error('Error copying assets:', err);
  process.exit(1);
}