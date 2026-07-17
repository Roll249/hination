import bcrypt from 'bcrypt';
import dotenv from 'dotenv';
import pg from 'pg';

dotenv.config();

const { Pool } = pg;

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'hination',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'hination',
});

async function seedAdmin() {
  const client = await pool.connect();
  
  try {
    const adminUsername = process.env.ADMIN_USERNAME || 'admin';
    const adminPassword = process.env.ADMIN_PASSWORD;
    
    if (!adminPassword) {
      console.error('ADMIN_PASSWORD not set in environment variables');
      console.error('Please set ADMIN_PASSWORD and run this script again');
      process.exit(1);
    }
    
    const passwordHash = await bcrypt.hash(adminPassword, 12);
    
    // Upsert admin user
    const result = await client.query(
      `INSERT INTO users (username, password_hash, role)
       VALUES ($1, $2, 'admin')
       ON CONFLICT (username) 
       DO UPDATE SET password_hash = $2, updated_at = NOW()
       RETURNING id, username, role`,
      [adminUsername, passwordHash]
    );
    
    console.log(`Admin user created/updated: ${result.rows[0].username}`);
    console.log('You can now log in with the configured credentials.');
    
  } catch (error) {
    console.error('Seed failed:', error);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

seedAdmin();
