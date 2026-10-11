import { mkdir, rm, cp, copyFile, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'dist');
if (path.dirname(output) !== root || path.basename(output) !== 'dist') throw new Error('Invalid build output directory');
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await copyFile(path.join(root, 'styles.css'), path.join(output, 'styles.css'));
for (const directory of ['src', 'assets']) await cp(path.join(root, directory), path.join(output, directory), { recursive: true });
await mkdir(path.join(output, 'research'), { recursive: true });
const snapshot = {};
for (const filename of ['timeline.zh-CN.json', 'bilibili-timeline.zh-CN.json', 'community-timeline.zh-CN.json', 'discussions.zh-CN.json', 'README.md', 'bilibili.md', 'community.md', 'discussions.md']) {
  const source = path.join(root, 'research', filename);
  const content = await readFile(source, 'utf8');
  if (filename.endsWith('.json')) snapshot['research/' + filename] = JSON.parse(content.replace(/^\uFEFF/, ''));
  await writeFile(path.join(output, 'research', filename), content);
}
snapshot['assets/covers/manifest.json'] = JSON.parse(await readFile(path.join(root, 'assets/covers/manifest.json'), 'utf8'));
const model = (await readFile(path.join(root, 'src/timeline.js'), 'utf8')).replace(/^export /gm, '');
const app = (await readFile(path.join(root, 'src/app.js'), 'utf8')).replace(/^import [^\n]+\n/, '');
const snapshotJSON = JSON.stringify(snapshot).replace(/</g, '\\u003c');
const bundledJS = (model + '\nconst esc = escapeHTML;\n' + app).replace(/<\/script/gi, '<\\/script');
const html = (await readFile(path.join(root, 'index.html'), 'utf8')).replace('<script type="module" src="src/app.js"></script>', `<script id="archive-data" type="application/json">${snapshotJSON}</script>\n    <script type="module">${bundledJS}</script>`);
await writeFile(path.join(output, 'index.html'), html);
console.log(`Static site built: ${output}\nSupports direct offline opening. Includes 4 research datasets, community quotes and original video covers.`);
