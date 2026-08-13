import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',webServer:[{command:'FIELDFIX_API_TARGET=http://127.0.0.1:18000 npm run dev -- --port 15173',port:15173,reuseExistingServer:false},{command:'FIELDFIX_E2E_API_PORT=18000 node scripts/start-e2e-backend.mjs',port:18000,reuseExistingServer:false}],use:{baseURL:'http://127.0.0.1:15173'}});
