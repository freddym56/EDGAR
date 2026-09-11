// db.js
// Server-side only DB/stub access (not used in arelle EDGAR plugin transform)
// (c) U.S. Securities and Exchange Commission, 17 U.S.C. 105

import * as fs from 'fs';                   // need sync + async APIs
import fsp from 'fs/promises';              // for readFile in stub
import path from 'node:path';
import { fileURLToPath } from 'node:url';

let adapterPromise; // singleton initializer
let mysqlPool;      // cached mysql2 pool (if used)

/**
 * Decide which DB adapter to use:
 *  - Try Neptune's Express module (../edgar_sql.js) first.
 *  - Fallback to mysql2/promise.
 */
async function initDbAdapter(runQuery) {
  if (!adapterPromise) {
    adapterPromise = (async () => {
        if (runQuery) {
        // Adapter that delegates to Neptune; no pool lifecycle
        return {
          name: 'neptune',
          open: async () => {},
          query: async (sql, values) => {
            const res = await runQuery(sql, values); // edgar_sql result
            // Normalize to [rows, fields]
            if (Array.isArray(res) && Array.isArray(res[0])) {
              return res;              // already [rows, fields]
            }
            if (Array.isArray(res)) {
              return [res, []];        // rows only
            }
            return [[res], []];         // single object -> wrap as one row
          },
          close: async () => {}
        };
      } else {
        // Not Neptune, such as dev1, use direct MySQL
        const mysql = await import('mysql2/promise');

        // Reuse a singleton pool
        if (!mysqlPool) {
          mysqlPool = mysql.createPool({
            host: process.env.DB_HOST,
            port: Number(process.env.DB_PORT || 3306),
            user: process.env.DB_USER,
            password: process.env.DB_PASS,
            database: process.env.DB_NAME,
            waitForConnections: true,
            connectionLimit: Number(process.env.DB_POOL_SIZE || 10),
            queueLimit: 0
          });
        }

        return {
          name: 'mysql2',
          open: async () => {},
          // Use execute for consistent prepared statements
          query: (sql, values) => mysqlPool.execute(sql, values),
          close: async () => {} // keep pool for entire process lifetime
        };
      }
    })();
  }
  return adapterPromise;
}

export async function getFilerDataMySQL(accessionNumberDashed, log_debug = () => {}, runQuery = null) {
  try {
    const adapter = await initDbAdapter(runQuery);
    log_debug(`DB adapter: ${adapter.name}; accession=${accessionNumberDashed}`);

    // Basic input validation
    if (typeof accessionNumberDashed !== 'string' || accessionNumberDashed.length < 10) {
      return { result: [], errors: ['Invalid accession number'] };
    }

    await adapter.open();

    // db health
    const [[{ version }]] = await adapter.query('SELECT VERSION() AS version');
    const [[{ dbname }]] = await adapter.query('SELECT DATABASE() AS dbname');
    log_debug(`DB ${adapter.name} version ${version} name ${dbname}`);

    // Primary query
    const [rows] = await adapter.query(
      `SELECT accession_number, filer_sequence, filer_type, filed_by_form_type,
              conformed_name, cik, assigned_sic, irs_number, state_of_incorporation,
              fiscal_year_end, street1, street2, city, state, zip, phone,
              m_street1, m_street2, m_city, m_state, m_zip, owner_org
       FROM filer WHERE accession_number = ?`,
      [accessionNumberDashed]
    );

    const result = Array.isArray(rows) ? rows : [];

    // Child queries per filer
    for (const r of result) {
      const [filingRows] = await adapter.query(
        `SELECT form_type, act, file_number, film_number
           FROM filing_values
          WHERE accession_number = ? AND cik = ? AND filer_type = ? AND filer_sequence = ?`,
        [r.accession_number, r.cik, r.filer_type, r.filer_sequence]
      );
      r.filing_info = Array.isArray(filingRows) ? filingRows : [];
    }

    await adapter.close();
    log_debug(`filing result = ${JSON.stringify(result)}`);
    return { result, errors: [] };
  } catch (e) {
    return { result: [], errors: [`Error loading filer data from database: ${e.message}`] };
  }
}

export async function getFilerDataStub(accessionNumberDashed) {
  try {
    const file = process.env.DB_STUB_FILE;
    if (!file) return { result: [], errors: ['DB_STUB_FILE not set'] };

    const buf = await fsp.readFile(file, 'utf-8');
    const data = JSON.parse(buf);
    const result = data[accessionNumberDashed] ?? data['default'] ?? [];
    return { result, errors: [] };
  } catch (e) {
    return { result: [], errors: [`Error loading stub data from json file: ${e.message}`] };
  }
}

export async function getFilerData(accessionNumberDashed, log_debug, runQuery = null) {
  // Keep your toggle behavior: if DB_STUB_FILE is defined, use stub
  if (process.env.DB_STUB_FILE) {
    return getFilerDataStub(accessionNumberDashed);
  }
  return getFilerDataMySQL(accessionNumberDashed, log_debug, runQuery);
}