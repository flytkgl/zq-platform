import { requestClient } from '#/api/request';

/**
 * 组织架构节点类型
 */
export interface OrgChartNode {
  id: string;
  name?: string;
  username: string;
  avatar?: string;
  dept_name?: string;
  post_name?: string;
  subordinate_count: number;
}

/**
 * 获取组织架构顶层节点
 */
export async function getOrgChartTopApi() {
  return requestClient.get<OrgChartNode[]>('/api/core/user/org-chart/top');
}

/**
 * 获取指定用户的组织架构节点
 */
export async function getOrgChartNodeApi(userId: string) {
  return requestClient.get<OrgChartNode>(`/api/core/user/org-chart/${userId}`);
}

/**
 * 汇报链节点（嵌套结构）
 */
export interface OrgChartChainNode extends OrgChartNode {
  children: OrgChartChainNode[];
}

/**
 * 获取用户汇报链（从顶层到当前用户的嵌套树）
 */
export async function getOrgChartChainApi(userId: string) {
  return requestClient.get<OrgChartChainNode>(
    `/api/core/user/org-chart/${userId}/chain`,
  );
}

/**
 * 获取组织架构子节点
 */
export async function getOrgChartChildrenApi(userId: string) {
  return requestClient.get<OrgChartNode[]>(
    `/api/core/user/org-chart/${userId}/children`,
  );
}
