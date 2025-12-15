# ⚡ Quick Start - 3-Phase Deployment

**Deploy antigravityCodeRed in 20-30 minutes**

---

## 🎯 Before You Start

✅ Do you have:
- [ ] Supabase account access
- [ ] Project ID: `xgcqjwviirrkyhwlaeyr`
- [ ] All 3 SQL files ready
- [ ] Stable internet connection
- [ ] 30 minutes of uninterrupted time

If you answered yes to all, let's begin!

---

## 🚀 Phase 1: Deploy Schema (5-10 minutes)

### Step 1: Open Supabase Dashboard
```
https://xgcqjwviirrkyhwlaeyr.supabase.co/dashboard
```

### Step 2: Navigate to SQL Editor
- Click "SQL Editor" in left sidebar
- Click "New Query"

### Step 3: Copy & Paste Schema
1. Open: `03_SCHEMA/0001_codered_base.sql`
2. Select all content (Cmd+A)
3. Copy (Cmd+C)
4. Paste into Supabase SQL Editor
5. Click "Run" button

### Step 4: Verify Success
You should see: `Executed successfully`

Look for message: "Multiple objects created"

### Step 5: Quick Verification Query
Paste this in a new SQL query to verify:

```sql
SELECT COUNT(*) as table_count 
FROM information_schema.tables 
WHERE table_schema = 'codered';
```

**Expected result:** `19` (19 tables created)

### ⏸️ If Something Goes Wrong
- Error: "Schema already exists" → This is fine! Continue to Phase 2
- Error: "Extension not found" → Contact Supabase support for pgvector
- Other error → Check details at end of this document

---

## 🚀 Phase 2: Seed Agents (1-2 minutes)

### Step 1: New Query in Supabase
- Click "New Query" (or clear previous query)

### Step 2: Copy & Paste Agent Script
1. Open: `01_DEPLOYMENT_SCRIPTS/seed-agents.sql`
2. Select all content
3. Copy
4. Paste into SQL Editor
5. Click "Run"

### Step 3: Verify Success
Expected message: `Executed successfully`

You should see the 5 agents listed:
- Architect Agent
- Code Agent
- Test Agent
- Review Agent
- Cynic Agent

### Step 4: Quick Verification Query
```sql
SELECT name, role, default_model 
FROM codered.agents 
ORDER BY created_at;
```

**Expected result:** 5 rows with agent details

### ⏸️ If Something Goes Wrong
- Error: "Table doesn't exist" → Phase 1 failed. Go back and check.
- Error: "Duplicate key" → Agents already exist. This is fine!
- Other error → See troubleshooting section

---

## 🚀 Phase 3: Setup RAG (1-2 minutes)

### Step 1: New Query in Supabase
- Click "New Query"

### Step 2: Copy & Paste RAG Script
1. Open: `01_DEPLOYMENT_SCRIPTS/setup-rag.sql`
2. Select all content
3. Copy
4. Paste into SQL Editor
5. Click "Run"

### Step 3: Verify Success
Expected message: `Executed successfully`

### Step 4: Quick Verification Query
```sql
SELECT proname 
FROM pg_proc 
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'codered')
AND proname IN ('search_embeddings', 'ingest_document', 'compute_similarity');
```

**Expected result:** 3 rows with function names

---

## ✅ Full Verification Checklist

After all 3 phases, run this comprehensive check:

```sql
SELECT 
  'Schema exists' as check,
  EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'codered') as passed
UNION ALL
SELECT '19 tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'codered') = 19
UNION ALL
SELECT '5 agents', (SELECT COUNT(*) FROM codered.agents) = 5
UNION ALL
SELECT 'pgvector extension', EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')
UNION ALL
SELECT 'search_embeddings function', EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'search_embeddings')
UNION ALL
SELECT 'ingest_document function', EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'ingest_document')
UNION ALL
SELECT '15+ indexes', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'codered') >= 15;
```

**Expected:** All rows should show `true` or `TRUE`

---

## 🎉 Deployment Complete!

Congratulations! You've successfully deployed antigravityCodeRed.

### What You Now Have:
✅ **19 database tables** (schema deployed)
✅ **5 AI agents** (Architect, Code, Test, Review, Cynic)
✅ **RAG system** (document search + semantic AI)
✅ **Cost tracking** (monitor agent spending)
✅ **Zone management** (red/yellow/green risk levels)

### Next Steps:
1. Read: `DEPLOYMENT_SUMMARY.txt` for detailed info
2. Create your first project in the database
3. Start ingesting documents for the RAG system
4. Assign agents to tasks

---

## 🆘 Troubleshooting Guide

### "Schema 'codered' already exists"
**What it means:** The schema was already created (maybe from a previous attempt)
**Solution:** This is fine! The SQL has "IF NOT EXISTS" clauses. Continue to Phase 2.

### "Extension 'vector' does not exist"
**What it means:** pgvector isn't enabled on your Supabase project
**Solution:** 
- Contact Supabase support to enable pgvector
- Or check if it's available: `SELECT * FROM pg_available_extensions WHERE name = 'vector';`

### "Permission denied" errors
**What it means:** Your Supabase credentials don't have the right permissions
**Solution:**
- Verify you're using the correct service key/token
- Check that your Supabase user has admin privileges
- Try logging out and logging back in

### SQL execution hangs (takes > 30 seconds)
**What it means:** The query is taking too long or the browser lost connection
**Solution:**
- Check your internet connection
- Refresh the Supabase dashboard
- Try executing the query again
- If it still hangs, check Supabase status: https://status.supabase.com

### "Table codered.agents doesn't exist" (in Phase 2)
**What it means:** Phase 1 didn't complete successfully
**Solution:**
- Go back to Phase 1
- Run the verification query: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'codered';`
- It should return 19. If not, Phase 1 failed.
- Rerun Phase 1 and watch for error messages.

### Functions not created in Phase 3
**What it means:** Either Phase 1 failed (missing pgvector) or Phase 3 didn't run completely
**Solution:**
- Check pgvector is installed: `SELECT extname FROM pg_extension;`
- If vector not in list, enable it first
- Then rerun Phase 3

### Agents not appearing in Phase 2
**What it means:** Either Phase 1 didn't create the agents table or Phase 2 didn't run
**Solution:**
- Verify Phase 1: `SELECT COUNT(*) FROM codered.agents;`
- If table doesn't exist, Phase 1 failed
- Rerun Phase 1 completely

---

## ⏱️ Expected Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Schema deployment | 5-10 min |
| 1 | Verification | 1 min |
| 2 | Agent seeding | 1-2 min |
| 2 | Verification | 1 min |
| 3 | RAG setup | 1-2 min |
| 3 | Verification | 1 min |
| - | Full verification | 2 min |
| **TOTAL** | | **20-30 min** |

---

## 📞 Need Help?

1. **Check the docs:**
   - `DEPLOYMENT_SUMMARY.txt` - Complete troubleshooting guide
   - `CODERED_DEPLOYMENT_GUIDE.md` - Detailed step-by-step
   - `RESOURCES_INDEX.md` - File reference

2. **Review the SQL:**
   - Each SQL file has comments explaining what it does
   - Read the SQL directly to understand the schema

3. **Contact Support:**
   - Supabase Issues: https://github.com/supabase/supabase/issues
   - PostgreSQL Issues: https://www.postgresql.org/support/

---

## 💡 Tips for Success

✅ **Do this:**
- Read this entire document before starting
- Have all 3 SQL files open
- Run verification queries after each phase
- Copy the entire file contents each time
- Wait for "Executed successfully" message

❌ **Don't do this:**
- Don't split up the SQL files or edit them
- Don't close your browser during execution
- Don't run phases out of order
- Don't modify the SQL before running
- Don't skip verification queries

---

## 🎯 You're Ready!

Follow the 3 phases above, and you'll have antigravityCodeRed deployed in 20-30 minutes.

**Start with Phase 1 now!** 🚀

---

*Questions? See DEPLOYMENT_SUMMARY.txt or README.md*
