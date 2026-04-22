#!/usr/bin/env node
'use strict';
/**
 * Writes backend/serverless.deploy.yml from backend/serverless.yml by resolving the
 * LAMBDA_VPC_* region between # LAMBDA_VPC_START / # LAMBDA_VPC_END.
 *
 * If LAMBDA_VPC_SUBNET_ID_1..3 and LAMBDA_VPC_SECURITY_GROUP_ID are all set → keep the
 * vpc block (env placeholders). If all empty → vpc: false. Partial config → exit 1.
 */
const fs = require('fs');
const path = require('path');

const backendDir = path.resolve(__dirname, '../backend');
const srcPath = path.join(backendDir, 'serverless.yml');
const outPath = path.join(backendDir, 'serverless.deploy.yml');

const MARKED_VPC_RE = /^  # LAMBDA_VPC_START\n([\s\S]*?)^  # LAMBDA_VPC_END\n/m;

function trim(s) {
  return (s && String(s).trim()) || '';
}

const s1 = trim(process.env.LAMBDA_VPC_SUBNET_ID_1);
const s2 = trim(process.env.LAMBDA_VPC_SUBNET_ID_2);
const s3 = trim(process.env.LAMBDA_VPC_SUBNET_ID_3);
const sg = trim(process.env.LAMBDA_VPC_SECURITY_GROUP_ID);

const filled = [s1, s2, s3, sg].filter(Boolean);
const enabled = Boolean(s1 && s2 && s3 && sg);

if (filled.length && !enabled) {
  console.error(
    'Lambda VPC: set all of LAMBDA_VPC_SUBNET_ID_1, LAMBDA_VPC_SUBNET_ID_2, LAMBDA_VPC_SUBNET_ID_3, LAMBDA_VPC_SECURITY_GROUP_ID, or leave all four unset for no VPC.'
  );
  process.exit(1);
}

const src = fs.readFileSync(srcPath, 'utf8');
const m = src.match(MARKED_VPC_RE);
if (!m) {
  console.error(
    `${srcPath} must contain a marked block:\n  # LAMBDA_VPC_START\n  vpc:\n    ...\n  # LAMBDA_VPC_END`
  );
  process.exit(1);
}

const replacement = enabled ? m[1] : '  vpc: false\n';
const out = src.replace(MARKED_VPC_RE, replacement);
fs.writeFileSync(outPath, out, 'utf8');
process.stderr.write(
  `${enabled ? 'Wrote' : 'Wrote (no Lambda VPC)'} ${outPath}\n`
);
