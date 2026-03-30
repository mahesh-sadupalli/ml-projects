import { PowerSyncDatabase } from '@powersync/web';
import { AppSchema } from '../types/schema';
import { SupabaseConnector } from './connector';

let db: PowerSyncDatabase | null = null;
let initPromise: Promise<PowerSyncDatabase> | null = null;

export function getDb(): Promise<PowerSyncDatabase> {
  if (db) return Promise.resolve(db);
  if (initPromise) return initPromise;

  initPromise = (async () => {
    console.log('[PowerSync] Creating database...');
    const instance = new PowerSyncDatabase({
      schema: AppSchema,
      database: { dbFilename: 'fieldsync.db' },
    });

    console.log('[PowerSync] Database created, waiting for ready...');
    // Some versions use init(), others auto-init. Try both.
    if (typeof instance.init === 'function') {
      await instance.init();
    }

    console.log('[PowerSync] Database ready');
    db = instance;
    return db;
  })();

  initPromise.catch(err => {
    console.error('[PowerSync] Init failed:', err);
    initPromise = null;
  });

  return initPromise;
}

export async function connectSync(): Promise<void> {
  const instance = await getDb();
  const connector = new SupabaseConnector();

  try {
    await instance.connect(connector);
    console.log('[PowerSync] Connected to sync service');
  } catch (err) {
    console.warn('[PowerSync] Sync connection failed, continuing in local-only mode:', err);
  }
}

export async function disconnectSync(): Promise<void> {
  const instance = await getDb();
  await instance.disconnect();
  console.log('[PowerSync] Disconnected from sync service');
}

export function generateId(): string {
  return crypto.randomUUID();
}
