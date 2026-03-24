import { useState, useEffect } from 'react'
import { useAuthStore } from '../lib/auth/store'
import { Users as UsersIcon, UserPlus, Shield, Edit2, Search, CheckCircle, XCircle, Trash2, Copy, Mail, AlertTriangle, RotateCcw, Eye, EyeOff } from 'lucide-react'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  must_change_password: boolean
  roles: string[]
  last_login?: string
  created_at: string
  is_deleted?: boolean
  deleted_at?: string
  deleted_by?: number
}

interface CreateUserData {
  username: string
  email: string
  password: string
  full_name?: string
  role_names: string[]
}

interface Toast {
  id: number
  type: 'success' | 'error' | 'info'
  message: string
}

export function UsersPage() {
  const { token, canManageUsers, isOwner } = useAuthStore()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false)
  const [showCreatedResult, setShowCreatedResult] = useState<{
    username: string; email: string; welcome_email_sent: boolean;
    delivery_mode: string; temporary_password?: string;
  } | null>(null)
  const [copied, setCopied] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{id: number, username: string} | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [showDeleted, setShowDeleted] = useState(false)
  const [restoreLoading, setRestoreLoading] = useState<number | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [newUser, setNewUser] = useState<CreateUserData>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role_names: ['VIEWER']
  })

  const addToast = (type: Toast['type'], message: string) => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }

  useEffect(() => {
    if (!canManageUsers()) {
      return
    }
    fetchUsers()
  }, [token, canManageUsers])

  useEffect(() => {
    fetchUsers()
  }, [showDeleted])

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams()
      if (showDeleted) {
        params.set('include_deleted', 'true')
        params.set('active_only', 'false')
      }
      const response = await fetch(`/api/users/?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
      }
    } catch (error) {
      console.error('Error fetching users:', error)
    } finally {
      setLoading(false)
    }
  }

  const createUser = async () => {
    try {
      const response = await fetch('/api/users/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUser)
      })

      if (response.ok) {
        const data = await response.json()
        setShowCreateModal(false)
        setNewUser({
          username: '',
          email: '',
          password: '',
          full_name: '',
          role_names: ['VIEWER']
        })
        fetchUsers()
        setShowCreatedResult({
          username: data.username,
          email: data.email,
          welcome_email_sent: data.welcome_email_sent ?? false,
          delivery_mode: data.delivery_mode ?? 'manual',
          temporary_password: data.temporary_password ?? undefined,
        })
        setCopied(false)
      } else {
        const errorData = await response.json()
        const errorMsg = typeof errorData.detail === 'string'
          ? errorData.detail
          : errorData.detail?.[0]?.msg || JSON.stringify(errorData.detail) || 'Failed to create user'
        addToast('error', errorMsg)
      }
    } catch (error) {
      console.error('Error creating user:', error)
      addToast('error', 'Failed to create user')
    }
  }

  const resetPassword = async () => {
    if (!selectedUserId || !newPassword) {
      addToast('error', 'Please enter a new password')
      return
    }

    try {
      const response = await fetch(`/api/users/${selectedUserId}/reset-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_password: newPassword })
      })

      if (response.ok) {
        addToast('success', 'Password reset successfully. User must change password on next login.')
        setShowResetPasswordModal(false)
        setSelectedUserId(null)
        setNewPassword('')
      } else {
        const error = await response.json()
        addToast('error', error.detail || 'Failed to reset password')
      }
    } catch (error) {
      console.error('Error resetting password:', error)
      addToast('error', 'Error resetting password')
    }
  }

  const toggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !currentStatus })
      })

      if (response.ok) {
        fetchUsers()
      }
    } catch (error) {
      console.error('Error updating user:', error)
    }
  }

  const openDeleteModal = (userId: number, username: string) => {
    setDeleteTarget({ id: userId, username })
    setShowDeleteModal(true)
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)

    try {
      const response = await fetch(`/api/users/${deleteTarget.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setShowDeleteModal(false)
        setDeleteTarget(null)
        fetchUsers()
        addToast('success', `User "${deleteTarget.username}" has been deleted`)
      } else {
        const error = await response.json()
        addToast('error', error.detail || 'Error deleting user')
      }
    } catch (error) {
      console.error('Error deleting user:', error)
      addToast('error', 'Error deleting user')
    } finally {
      setDeleteLoading(false)
    }
  }

  const restoreUser = async (userId: number, username: string) => {
    setRestoreLoading(userId)
    try {
      const response = await fetch(`/api/users/${userId}/restore`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        addToast('success', `User "${username}" has been restored`)
        fetchUsers()
      } else {
        const error = await response.json()
        addToast('error', error.detail || 'Error restoring user')
      }
    } catch (error) {
      console.error('Error restoring user:', error)
      addToast('error', 'Error restoring user')
    } finally {
      setRestoreLoading(null)
    }
  }

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (!canManageUsers()) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">You don't have permission to manage users. Required roles: OWNER or ADMIN</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <UsersIcon className="h-8 w-8 text-blue-600" />
              User Management
            </h1>
            <p className="mt-2 text-gray-600">Manage users, roles, and permissions</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            <UserPlus className="h-4 w-4" />
            Create User
          </button>
        </div>
      </div>

      {/* Search + Show Deleted Toggle */}
      <div className="mb-6 flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={() => setShowDeleted(!showDeleted)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition ${
            showDeleted
              ? 'bg-red-50 border-red-300 text-red-700 hover:bg-red-100'
              : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
          }`}
        >
          {showDeleted ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
          {showDeleted ? 'Showing deleted' : 'Show deleted'}
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Roles</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredUsers.map((user) => (
              <tr key={user.id} className={`hover:bg-gray-50 ${user.is_deleted ? 'bg-red-50 opacity-75' : ''}`}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${user.is_deleted ? 'bg-red-100' : 'bg-blue-100'}`}>
                      <span className={`font-semibold ${user.is_deleted ? 'text-red-600' : 'text-blue-600'}`}>{user.username[0].toUpperCase()}</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{user.username}</div>
                      {user.full_name && <div className="text-sm text-gray-500">{user.full_name}</div>}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{user.email}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex gap-1">
                    {user.roles.map((role) => (
                      <span
                        key={role}
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          role === 'OWNER' ? 'bg-purple-100 text-purple-800' :
                          role === 'ADMIN' ? 'bg-blue-100 text-blue-800' :
                          role === 'OPERATOR' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        <Shield className="h-3 w-3 mr-1" />
                        {role}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {user.is_deleted ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      <Trash2 className="h-3 w-3 mr-1" />
                      Deleted
                    </span>
                  ) : user.is_active ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      <XCircle className="h-3 w-3 mr-1" />
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {user.is_deleted ? (
                    /* Restore button for deleted users */
                    (isOwner() || canManageUsers()) && (
                      <button
                        onClick={() => restoreUser(user.id, user.username)}
                        className="inline-flex items-center gap-1 px-3 py-1 text-green-700 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition disabled:opacity-50"
                        disabled={restoreLoading === user.id}
                        title="Restore User"
                      >
                        <RotateCcw className={`h-4 w-4 ${restoreLoading === user.id ? 'animate-spin' : ''}`} />
                        {restoreLoading === user.id ? 'Restoring...' : 'Restore'}
                      </button>
                    )
                  ) : (
                    /* Normal action buttons */
                    <>
                      <button
                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        title="Toggle Active/Inactive"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUserId(user.id)
                          setShowResetPasswordModal(true)
                        }}
                        className="text-orange-600 hover:text-orange-900 mr-3"
                        title="Reset Password"
                      >
                        <Shield className="h-4 w-4" />
                      </button>
                      {(isOwner() || canManageUsers()) && (
                        <button
                          onClick={() => openDeleteModal(user.id, user.username)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete User"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Create New User</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                  placeholder="johndoe"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                  placeholder="john@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                  placeholder="Enter secure password"
                  required
                />
                <p className="text-xs text-gray-600 mt-1">{'\u2022'} Min 8 characters<br/>{'\u2022'} 1 uppercase (A-Z)<br/>{'\u2022'} 1 lowercase (a-z)<br/>{'\u2022'} 1 number (0-9)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
                <select
                  value={newUser.role_names[0]}
                  onChange={(e) => setNewUser({ ...newUser, role_names: [e.target.value] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                >
                  <option value="VIEWER">Viewer (Read Only)</option>
                  <option value="OPERATOR">Operator (Limited Write)</option>
                  <option value="ADMIN">Admin (Full Access)</option>
                </select>
              </div>
            </div>
            <div className="mt-6 flex gap-3">
              <button
                onClick={createUser}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Create User
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Created Result Modal */}
      {showCreatedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="text-green-600" size={28} />
              <h3 className="text-lg font-semibold text-gray-900">User Created Successfully</h3>
            </div>

            {showCreatedResult.welcome_email_sent ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Mail className="text-green-600" size={18} />
                  <span className="font-medium text-green-800">Welcome email sent</span>
                </div>
                <p className="text-sm text-green-700">
                  Credentials were sent to <strong>{showCreatedResult.email}</strong>.
                  The user must change their password on first login.
                </p>
              </div>
            ) : (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="text-amber-600" size={18} />
                  <span className="font-medium text-amber-800">SMTP unavailable &mdash; copy credentials now</span>
                </div>
                <p className="text-sm text-amber-700 mb-3">
                  The welcome email could not be sent. Please copy the credentials below and share them securely with the user. <strong>This is the only time the password will be shown.</strong>
                </p>
                <div className="bg-white border border-gray-200 rounded p-3 font-mono text-sm space-y-1">
                  <div><span className="text-gray-500">Username:</span> <strong className="text-gray-900">{showCreatedResult.username}</strong></div>
                  <div><span className="text-gray-500">Email:</span> <strong className="text-gray-900">{showCreatedResult.email}</strong></div>
                  {showCreatedResult.temporary_password && (
                    <div><span className="text-gray-500">Password:</span> <strong className="text-gray-900">{showCreatedResult.temporary_password}</strong></div>
                  )}
                </div>
                {showCreatedResult.temporary_password && (
                  <button
                    onClick={() => {
                      const text = `Username: ${showCreatedResult.username}\nEmail: ${showCreatedResult.email}\nPassword: ${showCreatedResult.temporary_password}\nNote: You must change your password on first login.`
                      navigator.clipboard.writeText(text).then(() => setCopied(true))
                    }}
                    className={`mt-3 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      copied ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {copied ? <><CheckCircle size={16} /> Copied to clipboard</> : <><Copy size={16} /> Copy credentials</>}
                  </button>
                )}
              </div>
            )}

            <button
              onClick={() => setShowCreatedResult(null)}
              className="w-full mt-4 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 font-medium"
            >
              Close
            </button>
          </div>
        </div>
      )}


      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4 shadow-xl">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Delete User</h3>
            </div>
            <p className="text-gray-600 mb-2">
              Are you sure you want to delete user <strong>{deleteTarget.username}</strong>?
            </p>
            <p className="text-sm text-gray-500 mb-6">
              The user will be deactivated and blocked from logging in. This action can be reverted by an administrator.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteTarget(null) }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                disabled={deleteLoading}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                disabled={deleteLoading}
              >
                {deleteLoading ? 'Deleting...' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}


      
      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4 shadow-xl">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Eliminar Usuario</h3>
            </div>
            <p className="text-gray-600 mb-2">
              \u00bfEst\u00e1 seguro que desea eliminar al usuario <strong>{deleteTarget.username}</strong>?
            </p>
            <p className="text-sm text-gray-500 mb-6">
              El usuario ser\u00e1 desactivado y no podr\u00e1 iniciar sesi\u00f3n. Esta acci\u00f3n puede ser revertida por un administrador.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteTarget(null) }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                disabled={deleteLoading}
              >
                Cancelar
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                disabled={deleteLoading}
              >
                {deleteLoading ? 'Eliminando...' : 'Eliminar Usuario'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Reset Password</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Password *</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 bg-white text-gray-900"
                  placeholder="Enter secure password"
                  required
                />
                <p className="text-xs text-gray-600 mt-1">{'\u2022'} Min 8 characters {'\u2022'} 1 uppercase {'\u2022'} 1 lowercase {'\u2022'} 1 number</p>
                <p className="text-xs text-orange-600 mt-1 font-medium">{'\u26A0\uFE0F'} User must change password on next login</p>
              </div>
            </div>
            <div className="mt-6 flex gap-3">
              <button
                onClick={resetPassword}
                className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                Reset Password
              </button>
              <button
                onClick={() => {
                  setShowResetPasswordModal(false)
                  setSelectedUserId(null)
                  setNewPassword('')
                }}
                className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-slide-in ${
              toast.type === 'success' ? 'bg-green-600 text-white' :
              toast.type === 'error' ? 'bg-red-600 text-white' :
              'bg-blue-600 text-white'
            }`}
          >
            {toast.type === 'success' && <CheckCircle className="h-4 w-4" />}
            {toast.type === 'error' && <XCircle className="h-4 w-4" />}
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}