'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Resource, ResourceHierarchy, ResourceStatistics } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plus, 
  Search, 
  TreePine, 
  Package, 
  Settings, 
  MoreHorizontal,
  Edit,
  Trash2,
  Move,
  Shield,
  ChevronDown,
  ChevronRight,
  Activity,
  Database
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from '@/hooks/use-toast';
import { CreateResourceDialog } from '@/components/resources/CreateResourceDialog';
import { EditResourceDialog } from '@/components/resources/EditResourceDialog';
import { DeleteResourceDialog } from '@/components/resources/DeleteResourceDialog';

interface ResourceTreeNodeProps {
  resource: ResourceHierarchy;
  level: number;
  onEdit: (resource: Resource) => void;
  onDelete: (resource: Resource) => void;
  onCreateChild: (parentId: string) => void;
}

function ResourceTreeNode({ resource, level, onEdit, onDelete, onCreateChild }: ResourceTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  
  const getTypeColor = (type: string) => {
    const colors = {
      product_family: 'bg-blue-100 text-blue-800',
      app: 'bg-green-100 text-green-800',
      capability: 'bg-purple-100 text-purple-800',
      service: 'bg-orange-100 text-orange-800',
      entity: 'bg-pink-100 text-pink-800',
      page: 'bg-yellow-100 text-yellow-800',
      api: 'bg-red-100 text-red-800'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'product_family': return '📦';
      case 'app': return '🎯';
      case 'capability': return '⚡';
      case 'service': return '🔧';
      case 'entity': return '📋';
      case 'page': return '📄';
      case 'api': return '🔌';
      default: return '📂';
    }
  };

  const hasChildren = resource.children && resource.children.length > 0;

  return (
    <div className="relative">
      <div 
        className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg group"
        style={{ paddingLeft: `${level * 24 + 12}px` }}
      >
        {hasChildren ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        ) : (
          <div className="h-6 w-6" />
        )}

        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-lg">{getTypeIcon(resource.type)}</span>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-gray-900 truncate">{resource.name}</h4>
              <Badge variant="outline" className={getTypeColor(resource.type)}>
                {resource.type.replace('_', ' ')}
              </Badge>
              {!resource.is_active && (
                <Badge variant="secondary">Inactive</Badge>
              )}
            </div>
            <p className="text-sm text-gray-500 truncate">{resource.code}</p>
            {resource.description && (
              <p className="text-sm text-gray-600 mt-1 truncate">{resource.description}</p>
            )}
          </div>

          {resource.permission_count !== undefined && (
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {resource.permission_count} permissions
            </Badge>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(resource)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onCreateChild(resource.id)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Child
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onDelete(resource)}>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {resource.children!.map((child) => (
            <ResourceTreeNode
              key={child.id}
              resource={child}
              level={level + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              onCreateChild={onCreateChild}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function StatisticsCards({ stats }: { stats: ResourceStatistics }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Resources</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.total_resources || 0}</div>
          <p className="text-xs text-muted-foreground">
            {stats?.active_resources || 0} active
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Max Depth</CardTitle>
          <TreePine className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.max_depth || 0}</div>
          <p className="text-xs text-muted-foreground">
            hierarchy levels
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Permissions</CardTitle>
          <Shield className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.total_permissions || 0}</div>
          <p className="text-xs text-muted-foreground">
            total permissions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Resource Types</CardTitle>
          <Package className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {Object.keys(stats?.resources_by_type || {}).length}
          </div>
          <p className="text-xs text-muted-foreground">
            different types
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export function ResourcesManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [resourceToDelete, setResourceToDelete] = useState<Resource | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [parentIdForCreate, setParentIdForCreate] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch resource tree
  const { data: resourceTree, isLoading: treeLoading } = useQuery({
    queryKey: ['resources', 'tree'],
    queryFn: () => apiClient.resources.getTree(),
  });

  // Fetch resource statistics
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ['resources', 'statistics'],
    queryFn: () => apiClient.resources.getStatistics(),
  });

  // Fetch flat resource list for search
  const { data: resourcesList, isLoading: listLoading } = useQuery({
    queryKey: ['resources', 'list', searchTerm],
    queryFn: () => apiClient.resources.list({ 
      search: searchTerm || undefined,
      limit: 100 
    }),
    enabled: !!searchTerm,
  });

  const refreshData = () => {
    queryClient.invalidateQueries({ queryKey: ['resources'] });
  };

  const handleEdit = (resource: Resource) => {
    setSelectedResource(resource);
    setEditDialogOpen(true);
  };

  const handleDelete = (resource: Resource) => {
    setResourceToDelete(resource);
    setDeleteDialogOpen(true);
  };

  const handleCreateChild = (parentId: string) => {
    setParentIdForCreate(parentId);
    setCreateDialogOpen(true);
  };

  const handleCreateRoot = () => {
    setParentIdForCreate(null);
    setCreateDialogOpen(true);
  };

  if (statsLoading || treeLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Resources</h1>
          <p className="text-gray-600">Manage your hierarchical resource structure</p>
        </div>
        <Button onClick={handleCreateRoot}>
          <Plus className="mr-2 h-4 w-4" />
          Create Resource
        </Button>
      </div>

      {/* Statistics */}
      {statistics?.data && <StatisticsCards stats={statistics.data} />}

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Resource Hierarchy</CardTitle>
          <CardDescription>
            View and manage your resource hierarchy. Resources can be organized as: 
            Product Family → App → Capability → Service
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search resources..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <Tabs defaultValue="tree" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="tree">Tree View</TabsTrigger>
              <TabsTrigger value="list">List View</TabsTrigger>
            </TabsList>
            
            <TabsContent value="tree" className="space-y-4">
              {resourceTree && resourceTree.data ? (
                <div className="space-y-2">
                  {resourceTree.data.resources.map((resource: ResourceHierarchy) => (
                    <ResourceTreeNode
                      key={resource.id}
                      resource={resource}
                      level={0}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onCreateChild={handleCreateChild}
                    />
                  ))}
                  {resourceTree.data.resources.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium mb-2">No resources found</h3>
                      <p className="mb-4">Get started by creating your first resource.</p>
                      <Button onClick={handleCreateRoot}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Resource
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="list" className="space-y-4">
              {searchTerm && resourcesList ? (
                <div className="grid gap-4">
                  {resourcesList.data.resources.map((resource: Resource) => (
                    <Card key={resource.id}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-lg">
                              {resource.type === 'product_family' ? '📦' :
                               resource.type === 'app' ? '🎯' :
                               resource.type === 'capability' ? '⚡' :
                               resource.type === 'service' ? '🔧' :
                               resource.type === 'entity' ? '📋' :
                               resource.type === 'page' ? '📄' :
                               resource.type === 'api' ? '🔌' : '📂'}
                            </span>
                            <div>
                              <h4 className="font-medium">{resource.name}</h4>
                              <p className="text-sm text-gray-500">{resource.code}</p>
                            </div>
                            <Badge variant="outline">
                              {resource.type.replace('_', ' ')}
                            </Badge>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleEdit(resource)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDelete(resource)}>
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p>Enter a search term to view resources in list format</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <CreateResourceDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        parentId={parentIdForCreate}
        onSuccess={refreshData}
      />

      {selectedResource && (
        <EditResourceDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          resource={selectedResource}
          onSuccess={refreshData}
        />
      )}

      {resourceToDelete && (
        <DeleteResourceDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          resource={resourceToDelete}
          onSuccess={refreshData}
        />
      )}
    </div>
  );
}