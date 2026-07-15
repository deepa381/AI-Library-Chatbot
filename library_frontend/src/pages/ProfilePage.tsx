import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/auth';
import { borrowApi } from '../api/borrow';
import { reservationsApi } from '../api/reservations';
import { Skeleton } from '../components/ui/skeleton';
import { User as UserIcon, Mail, Calendar, Settings, Phone, Building, Shield, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'react-hot-toast';

export function ProfilePage() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    department: '',
  });

  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.getProfile,
  });

  const { data: borrows } = useQuery({
    queryKey: ['borrows'],
    queryFn: borrowApi.getBorrows,
  });

  const { data: reservations } = useQuery({
    queryKey: ['reservations'],
    queryFn: reservationsApi.getReservations,
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        phone: profile.profile?.phone || '',
        department: profile.profile?.department || '',
      });
    }
  }, [profile]);

  if (isProfileLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await authApi.updateProfile(formData);
      toast.success('Profile updated successfully');
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to update profile');
    }
  };

  const activeBorrowsCount = borrows?.filter(b => b.status === 'BORROWED' || b.status === 'OVERDUE').length ?? 0;
  const totalBorrowsCount = borrows?.length ?? 0;
  const activeReservationsCount = reservations?.filter(r => r.status === 'WAITING' || r.status === 'ACTIVE').length ?? 0;

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Profile</h1>
        <p className="text-muted-foreground mt-1">Manage your account and preferences.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Profile Details Card */}
        <div className="rounded-xl border bg-card p-6 shadow-sm flex flex-col">
          <div className="flex flex-col items-center text-center border-b pb-6 mb-6">
            <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <UserIcon className="h-10 w-10 text-primary" />
            </div>
            <h2 className="text-2xl font-bold">{profile?.first_name} {profile?.last_name}</h2>
            <p className="text-muted-foreground text-sm">@{profile?.username}</p>
            <div className="mt-2 flex items-center gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                profile?.profile?.role === 'LIBRARIAN' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
              }`}>
                <Shield className="mr-1 h-3 w-3" />
                {profile?.profile?.role}
              </span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                profile?.profile?.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
              }`}>
                {profile?.profile?.is_active ? (
                  <>
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Active
                  </>
                ) : (
                  <>
                    <XCircle className="mr-1 h-3 w-3" />
                    Inactive
                  </>
                )}
              </span>
            </div>
          </div>

          {isEditing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">First Name</label>
                  <Input
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Last Name</label>
                  <Input
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Phone</label>
                <Input
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Department</label>
                <Input
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                />
              </div>
              <div className="flex gap-2 pt-2">
                <Button type="submit" className="flex-1">Save Changes</Button>
                <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4 flex-1">
              <div className="grid grid-cols-2 gap-4 text-sm border-b pb-4">
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Email Address</p>
                  <div className="flex items-center mt-1">
                    <Mail className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.email || 'No email provided'}</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Membership ID</p>
                  <div className="flex items-center mt-1">
                    <Shield className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.profile?.membership_id || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm border-b pb-4">
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Phone</p>
                  <div className="flex items-center mt-1">
                    <Phone className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.profile?.phone || 'No phone provided'}</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Department</p>
                  <div className="flex items-center mt-1">
                    <Building className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.profile?.department || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm pb-4">
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Membership Type</p>
                  <div className="flex items-center mt-1">
                    <Shield className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.profile?.membership_type || 'STANDARD'}</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs uppercase tracking-wider">Borrow Limit</p>
                  <div className="flex items-center mt-1">
                    <Building className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{profile?.profile?.borrow_limit ?? 5} books</span>
                  </div>
                </div>
              </div>

              {profile?.profile?.created_at && (
                <div className="flex items-center text-xs text-muted-foreground pt-2">
                  <Calendar className="mr-2 h-3.5 w-3.5" />
                  <span>Joined library on {new Date(profile.profile.created_at).toLocaleDateString()}</span>
                </div>
              )}

              <Button onClick={() => setIsEditing(true)} variant="outline" className="w-full mt-4">
                <Settings className="mr-2 h-4 w-4" />
                Edit Profile
              </Button>
            </div>
          )}
        </div>

        {/* Reading Overview Card */}
        <div className="rounded-xl border bg-card p-6 shadow-sm space-y-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-semibold border-b pb-2 mb-4">Reading Overview</h3>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-muted/50 text-center">
                <div className="text-2xl font-bold text-primary">{totalBorrowsCount}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mt-1">Total Borrows</div>
              </div>
              <div className="p-4 rounded-lg bg-muted/50 text-center">
                <div className="text-2xl font-bold text-emerald-500">{activeBorrowsCount}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mt-1">Active Borrows</div>
              </div>
              <div className="p-4 rounded-lg bg-muted/50 text-center">
                <div className="text-2xl font-bold text-amber-500">{activeReservationsCount}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mt-1">Active Reservations</div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Favorite Categories</h4>
            <div className="flex flex-wrap gap-2">
              {['Technology', 'Science', 'Literature'].map(cat => (
                <span key={cat} className="px-3 py-1 bg-secondary text-secondary-foreground text-xs rounded-full">
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
