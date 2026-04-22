'use strict';

/**
 * Builds provider.vpc from comma-separated env vars (read at deploy/package time).
 * Synchronous so Serverless always sees a plain object (not a Promise).
 */
function parseCommaList(raw) {
  return String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

module.exports = () => {
  const subnetIds = parseCommaList(process.env.LAMBDA_VPC_SUBNET_IDS);
  const securityGroupIds = parseCommaList(process.env.LAMBDA_VPC_SECURITY_GROUP_IDS);
  if (!subnetIds.length || !securityGroupIds.length) return {};
  return { subnetIds, securityGroupIds };
};
