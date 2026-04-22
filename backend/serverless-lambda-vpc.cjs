'use strict';

/**
 * Builds provider.vpc from env:
 * - Prefer managed RDS access: LAMBDA_VPC_SUBNET_IDS + RDS_VPC_ID + RDS_SECURITY_GROUP_ID
 *   → securityGroupIds reference stack resource LambdaRdsConnectivitySecurityGroup.
 * - Else: LAMBDA_VPC_SUBNET_IDS + LAMBDA_VPC_SECURITY_GROUP_IDS (comma-separated) for manual SGs.
 * Omits VPC when subnets are empty or no SGs can be resolved.
 */
function parseCommaList(raw) {
  return String(raw || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

module.exports = async () => {
  const subnetIds = parseCommaList(process.env.LAMBDA_VPC_SUBNET_IDS);
  if (!subnetIds.length) return {};

  const rdsVpcId = String(process.env.RDS_VPC_ID || '').trim();
  const rdsSgId = String(process.env.RDS_SECURITY_GROUP_ID || '').trim();
  const useManagedRdsSg = Boolean(rdsVpcId && rdsSgId);

  if (useManagedRdsSg) {
    return {
      subnetIds,
      securityGroupIds: [{ Ref: 'LambdaRdsConnectivitySecurityGroup' }],
    };
  }

  const manualSgs = parseCommaList(process.env.LAMBDA_VPC_SECURITY_GROUP_IDS);
  if (!manualSgs.length) return {};

  return { subnetIds, securityGroupIds: manualSgs };
};
