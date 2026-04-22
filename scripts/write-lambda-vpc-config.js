#!/usr/bin/env node
'use strict';
/**
 * Writes backend/lambda-vpc.config.json from LAMBDA_VPC_SUBNET_IDS and
 * LAMBDA_VPC_SECURITY_GROUP_IDS (comma-separated). Used in CI so Serverless
 * reads VPC ids from disk (reliable); removes the file when either list is empty.
 */
const fs = require('fs');
const path = require('path');

const out = path.resolve(__dirname, '../backend/lambda-vpc.config.json');
const parse = (raw) =>
  String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

const subnetIds = parse(process.env.LAMBDA_VPC_SUBNET_IDS);
const securityGroupIds = parse(process.env.LAMBDA_VPC_SECURITY_GROUP_IDS);

if (subnetIds.length && securityGroupIds.length) {
  fs.writeFileSync(out, JSON.stringify({ subnetIds, securityGroupIds }, null, 0));
  process.stderr.write(`Wrote ${out} (${subnetIds.length} subnets, ${securityGroupIds.length} SGs)\n`);
} else {
  try {
    fs.unlinkSync(out);
  } catch (_) {
    /* absent is fine */
  }
  process.stderr.write(
    'No backend/lambda-vpc.config.json (both LAMBDA_VPC_SUBNET_IDS and LAMBDA_VPC_SECURITY_GROUP_IDS must be non-empty)\n'
  );
}
