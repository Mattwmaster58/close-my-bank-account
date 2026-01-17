import fs from 'fs';
import path from 'path';

const metadataPath = path.join(process.cwd(), 'static', 'metadata.json');

const metadata = {
  lastUpdated: Date.now()
};

fs.writeFileSync(metadataPath, JSON.stringify(metadata), 'utf-8');
