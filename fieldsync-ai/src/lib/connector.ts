import type {
  AbstractPowerSyncDatabase,
  CrudEntry,
  PowerSyncBackendConnector,
} from '@powersync/web';
import { UpdateType } from '@powersync/web';
import { supabase } from './supabase';

// Maps PowerSync table names to Supabase table names
const TABLE_MAP: Record<string, string> = {
  entries: 'entries',
  projects: 'projects',
  ai_insights: 'ai_insights',
};

export class SupabaseConnector implements PowerSyncBackendConnector {
  async fetchCredentials() {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      throw new Error('Not authenticated');
    }

    const powersyncUrl = import.meta.env.VITE_POWERSYNC_URL as string;
    if (!powersyncUrl) {
      throw new Error('PowerSync URL not configured');
    }

    return {
      endpoint: powersyncUrl,
      token: session.access_token,
    };
  }

  async uploadData(database: AbstractPowerSyncDatabase): Promise<void> {
    const transaction = await database.getNextCrudTransaction();

    if (!transaction) return;

    try {
      for (const op of transaction.crud) {
        await this.applyOperation(op);
      }
      await transaction.complete();
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  }

  private async applyOperation(op: CrudEntry): Promise<void> {
    const table = TABLE_MAP[op.table] || op.table;

    // Convert tags/media_urls from string to JSONB for Supabase
    const data = { ...op.opData };
    if (data && table === 'entries') {
      if (typeof data.tags === 'string') {
        try { data.tags = JSON.parse(data.tags); } catch { /* keep as string */ }
      }
      if (typeof data.media_urls === 'string') {
        try { data.media_urls = JSON.parse(data.media_urls); } catch { /* keep as string */ }
      }
    }

    switch (op.op) {
      case UpdateType.PUT: {
        const { error } = await supabase
          .from(table)
          .upsert({ id: op.id, ...data });
        if (error) throw error;
        break;
      }
      case UpdateType.PATCH: {
        const { error } = await supabase
          .from(table)
          .update(data)
          .eq('id', op.id);
        if (error) throw error;
        break;
      }
      case UpdateType.DELETE: {
        const { error } = await supabase
          .from(table)
          .delete()
          .eq('id', op.id);
        if (error) throw error;
        break;
      }
    }
  }
}
