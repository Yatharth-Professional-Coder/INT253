const fs = require('fs');
const { execSync } = require('child_process');

const root = 'c:/LPU/SEM 7/INT 253/INT253';
const skillDir = 'C:/Users/aarti/.gemini/config/plugins/understand-anything/skills/understand';
const batchesData = JSON.parse(fs.readFileSync(root + '/.ua/intermediate/batches.json', 'utf8'));

batchesData.batches.forEach((batch, i) => {
  const input = {
    projectRoot: root,
    batchFiles: batch.files,
    batchImportData: batch.batchImportData || {}
  };
  const inPath = root + '/.ua/tmp/ua-file-analyzer-input-' + i + '.json';
  const outPath = root + '/.ua/tmp/ua-file-extract-results-' + i + '.json';
  fs.writeFileSync(inPath, JSON.stringify(input, null, 2));

  console.log('Running extract-structure for batch ' + i + ' (' + batch.files.length + ' files)...');
  execSync(`node "${skillDir}/extract-structure.mjs" "${inPath}" "${outPath}"`, { stdio: 'inherit' });
});
