'use strict';

/**
 * Builds provider.vpc from comma-separated env vars.
 * Use the same security group(s) as the RDS instance (see collect-gha-env.sh).
 */
function parseCommaList(raw) {
  return String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

module.exports = async () => {
  const subnetIds = parseCommaList(process.env.LAMBDA_VPC_SUBNET_IDS);
  const securityGroupIds = parseCommaList(process.env.LAMBDA_VPC_SECURITY_GROUP_IDS);
  if (!subnetIds.length || !securityGroupIds.length) return {};
  return { subnetIds, securityGroupIds };
};
