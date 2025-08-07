import { UsersManagement } from '@/components/dashboard/UsersManagement';

export default function UsersPage() {
  return <UsersManagement />;
}

export const metadata = {
  title: 'Users - Sentinel',
  description: 'Manage users and their permissions',
};