'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Plus, MoreHorizontal, UsersRound, Users, FolderTree } from 'lucide-react';
import { Group } from '@/types';
import { CreateGroupDialog } from '@/components/groups/CreateGroupDialog';
import { EditGroupDialog } from '@/components/groups/EditGroupDialog';

export function GroupsManagement() {
  const [searchTerm, setSearchTerm] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const { userRole } = useAuthStore();

  const canManageGroups = userRole === 'super_admin' || userRole === 'tenant_admin';

  // Fetch groups from API
  const {
    data: groupsResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['groups'],
    queryFn: () => apiClient.groups.list(),
    retry: 1,
  });

  const groups: Group[] = groupsResponse?.items || groupsResponse || [];

  const filteredGroups = groups.filter((group: Group) =>
    `${group.display_name || group.name} ${group.description} ${group.name}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Group Management</h1>
            <p className="text-gray-600">Loading groups...</p>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Group Management</h1>
            <p className="text-gray-600">Unable to load groups</p>
          </div>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <p className="text-red-600">Failed to load groups. Please try again.</p>
              <p className="text-gray-500 mt-2">Error: {error?.message || 'Unknown error'}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getGroupIcon = (group: Group) => {
    if (group.parent_group_id) {
      return <FolderTree className="h-4 w-4 text-blue-600" />;
    }
    return <UsersRound className="h-4 w-4 text-blue-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Group Management</h1>
          <p className="text-gray-600">
            Organize users with hierarchical groups and role assignments
          </p>
        </div>
        {canManageGroups && (
          <Button 
            className="bg-blue-600 hover:bg-blue-700"
            onClick={() => setCreateDialogOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Group
          </Button>
        )}
      </div>

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Groups</CardTitle>
              <CardDescription>
                {filteredGroups.length} group{filteredGroups.length !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search groups..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>Group</TableHead>
                  <TableHead>Parent Group</TableHead>
                  <TableHead>Members</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  {canManageGroups && (
                    <TableHead className="w-[50px]">Actions</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredGroups.map((group) => (
                  <TableRow key={group.id}>
                    <TableCell>
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        {getGroupIcon(group)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{group.display_name || group.name}</div>
                        <div className="text-sm text-gray-500">{group.description}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          ID: {group.name}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {group.parent_group_id ? (
                        <Badge variant="outline" className="bg-gray-50">
                          Parent Group
                        </Badge>
                      ) : (
                        <span className="text-gray-400 text-sm">Root Group</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center text-sm">
                        <Users className="mr-1 h-3 w-3 text-gray-400" />
                        0 {/* TODO: Add member count from API */}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={group.is_active ? "default" : "secondary"}
                        className={
                          group.is_active
                            ? "bg-green-100 text-green-800 hover:bg-green-100"
                            : "bg-gray-100 text-gray-800 hover:bg-gray-100"
                        }
                      >
                        {group.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatDate(group.created_at)}
                    </TableCell>
                    {canManageGroups && (
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {groups.length}
            </div>
            <p className="text-xs text-gray-500">All groups</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Root Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {groups.filter((g: Group) => !g.parent_group_id).length}
            </div>
            <p className="text-xs text-gray-500">Top-level groups</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Active Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {groups.filter((g: Group) => g.is_active).length}
            </div>
            <p className="text-xs text-gray-500">Currently active</p>
          </CardContent>
        </Card>
      </div>

      {/* Dialogs */}
      <CreateGroupDialog 
        open={createDialogOpen} 
        onOpenChange={setCreateDialogOpen} 
      />
      <EditGroupDialog 
        open={editDialogOpen} 
        onOpenChange={setEditDialogOpen}
        group={selectedGroup}
      />
    </div>
  );
}