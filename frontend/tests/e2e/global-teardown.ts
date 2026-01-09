import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function globalTeardown() {
  const dbPath = resolve(__dirname, '../../../backend/data/trading_wizard.db');
  
  try {
    const db = new Database(dbPath);
    
    db.exec(`
      DELETE FROM simulation_sessions WHERE user_id IN (
        SELECT id FROM users WHERE fingerprint LIKE 'test_%' OR created_at > datetime('now', '-1 hour')
      );
      DELETE FROM users WHERE fingerprint LIKE 'test_%' OR created_at > datetime('now', '-1 hour');
    `);
    
    db.close();
    console.log('Test users cleaned up from database');
  } catch {
    console.warn('Failed to clean up test users');
  }
}

export default globalTeardown;
