export type NodeType = 'P' | 'C' | 'M' | 'D';

export type RelationshipType =
  | 'INSTANTIATES'
  | 'ANALOGOUS_TO'
  | 'DEPENDS_ON'
  | 'PART_OF'
  | 'CONTRASTS_WITH'
  | 'DERIVED_FROM';

export type NodeStatus = 'draft' | 'confirmed' | 'rejected';

export type SpaceType = 'personal' | 'group';

export type GroupRole = 'owner' | 'admin' | 'member' | 'viewer';
