import { useState, useEffect, useCallback } from 'react'
import { useAuthStore } from '../lib/auth/store'
import {
  Users as UsersIcon, UserPlus, Shield, Search, CheckCircle,
  XCircle, Trash2, AlertTriangle,
  Crown, Wrench, BookOpen, Pencil, Key, Mail
} from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface User {
  id: number; username: string; email: string; full_name?: string
  is_active: boolean; must_change_password: boolean; roles: string[]
  last_login?: string; created_at: string
}
interface CreateUserData {
  username: string; email: string; password: string
  full_name?: string; role_names: string[]
}
interface Toast { id: number; type: 'success' | 'error' | 'info'; message: string }
interface RoleMeta { name: string; description: string; level: number; assignable: boolean }

const ROLE_META: Record<string, { label: string; desc: string; color: string; bg: string; icon: any }> = {
  OWNER:    { label: 'Owner',    desc: 'License holder with full platform control',  color: 'text-amber-800',  bg: 'bg-amber-50 border-amber-200',   icon: Crown },
  ADMIN:    { label: 'Admin',    desc: 'Operational administrator',                  color: 'text-indigo-800', bg: 'bg-indigo-50 border-indigo-200',  icon: Shield },
  OPERATOR: { label: 'Operator', desc: 'Handles monitoring, alerts, incidents',      color: 'text-emerald-800',bg: 'bg-emerald-50 border-emerald-200',icon: Wrench },
  VIEWER:   { label: 'Viewer',   desc: 'Read-only access',                           color: 'text-slate-700',  bg: 'bg-slate-50 border-slate-200',    icon: BookOpen },
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function UsersPage() {
  const { token, canManageUsers, isOwner } = useAuthStore()

  const [users,       setUsers]       = useState<User[]>([])
  const [loading,     setLoading]     = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [toasts,      setToasts]      = useState<Toast[]>([])

  // Modals
  const [showCreateModal,   setShowCreateModal]   = useState(false)
  const [showEditModal,     setShowEditModal]     = useState(false)
  const [showDeleteModal,   setShowDeleteModal]   = useState(false)
  const [showResetPwModal,  setShowResetPwModal]  = useState(false)
  const [showCreatedResult, setShowCreatedResult] = useState<{
    username: string; email: string; welcome_email_sent: boolean
    delivery_mode: string
  } | null>(null)

  // Working state
  const [editTarget,   setEditTarget]   = useState<User | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; username: string } | null>(null)
  const [pwUserId,     setPwUserId]     = useState<number | null>(null)
  const [newPassword,  setNewPassword]  = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  // Roles from backend
  const [availableRoles, setAvailableRoles] = useState<RoleMeta[]>([])

  // Forms
  const [newUser, setNewUser] = useState<CreateUserData>({
    username: '', email: '', password: '', full_name: '', role_names: ['VIEWER'],
  })
  const [editForm, setEditForm] = useState({ full_name: '', email: '', role_name: '' })

  const addToast = (type: Toast['type'], message: string) => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4500)
  }

  /* ---------- data fetching ---------- */

  const fetchUsers = useCallback(async () => {
    try {
      const r = await fetch('/api/users/', { headers: { Authorization: `Bearer ${token}` } })
      if (r.ok) { const d = await r.json(); setUsers(d.users || []) }
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [token])

  const fetchRoles = useCallback(async () => {
    try {
      const r = await fetch('/api/users/meta/roles', { headers: { Authorization: `Bearer ${token}` } })
      if (r.ok) { const d = await r.json(); setAvailableRoles(d.roles || []) }
    } catch { /* */ }
  }, [token])

  useEffect(() => { if (canManageUsers()) { fetchUsers(); fetchRoles() } }, [canManageUsers, fetchUsers, fetchRoles])

  /* ---------- actions ---------- */

  const createUser = async () => {
    setActionLoading(true)
    try {
      const r = await fetch('/api/users/', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser),
      })
      if (r.ok) {
        const d = await r.json()
        setShowCreateModal(false)
        setNewUser({ username: '', email: '', password: '', full_name: '', role_names: ['VIEWER'] })
        fetchUsers()
        setShowCreatedResult({
          username: d.username, email: d.email,
          welcome_email_sent: d.welcome_email_sent ?? false,
          delivery_mode: d.delivery_mode ?? 'manual',
        })
      } else {
        const e = await r.json()
        addToast('error', typeof e.detail === 'string' ? e.detail : e.detail?.[0]?.msg || 'Failed to create user')
      }
    } catch { addToast('error', 'Failed to create user') }
    finally { setActionLoading(false) }
  }

  const saveEdit = async () => {
    if (!editTarget) return
    setActionLoading(true)
    try {
      const body: any = {}
      if (editForm.full_name !== (editTarget.full_name || '')) body.full_name = editForm.full_name
      if (editForm.email !== editTarget.email) body.email = editForm.email
      if (editForm.role_name && editForm.role_name !== editTarget.roles[0]) body.role_name = editForm.role_name
      const r = await fetch(`/api/users/${editTarget.id}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (r.ok) {
        setShowEditModal(false); setEditTarget(null); fetchUsers()
        addToast('success', `User "${editTarget.username}" updated (synced to Keycloak)`)
      } else {
        const e = await r.json()
        addToast('error', typeof e.detail === 'string' ? e.detail : Array.isArray(e.detail) ? e.detail.map((d: any) => d.msg || d).join(', ') : 'Update failed')
      }
    } catch { addToast('error', 'Update failed') }
    finally { setActionLoading(false) }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setActionLoading(true)
    try {
      const r = await fetch(`/api/users/${deleteTarget.id}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${token}` },
      })
      if (r.ok) {
        setShowDeleteModal(false); setDeleteTarget(null); fetchUsers()
        addToast('success', `User "${deleteTarget.username}" permanently deleted`)
      } else {
        const e = await r.json(); addToast('error', e.detail || 'Delete failed')
      }
    } catch { addToast('error', 'Delete failed') }
    finally { setActionLoading(false) }
  }

  const resetPassword = async () => {
    if (!pwUserId || !newPassword) { addToast('error', 'Enter a password'); return }
    setActionLoading(true)
    try {
      const r = await fetch(`/api/users/${pwUserId}/reset-password`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: newPassword }),
      })
      if (r.ok) {
        addToast('success', 'Password reset in Keycloak. User must change on next login.')
        setShowResetPwModal(false); setPwUserId(null); setNewPassword('')
      } else {
        const e = await r.json().catch(() => ({ detail: 'Reset failed' })); const msg = Array.isArray(e.detail) ? e.detail.map((d: any) => d.msg || d).join(', ') : (e.detail || 'Reset failed'); addToast('error', msg)
      }
    } catch { addToast('error', 'Reset failed') }
    finally { setActionLoading(false) }
  }

  const sendResetEmail = async () => {
    if (!pwUserId) return
    setActionLoading(true)
    try {
      const r = await fetch(`/api/users/${pwUserId}/send-reset-email`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (r.ok) {
        addToast('success', 'Password reset email sent via Keycloak')
        setShowResetPwModal(false); setPwUserId(null); setNewPassword('')
      } else {
        const e = await r.json().catch(() => ({ detail: 'Failed to send reset email' })); const emailMsg = Array.isArray(e.detail) ? e.detail.map((d: any) => d.msg || d).join(', ') : (e.detail || 'Failed to send reset email'); addToast('error', emailMsg)
      }
    } catch { addToast('error', 'Failed to send reset email') }
    finally { setActionLoading(false) }
  }

  const toggleActive = async (uid: number, active: boolean) => {
    try {
      const r = await fetch(`/api/users/${uid}`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !active }),
      })
      if (r.ok) {
        fetchUsers()
        addToast('success', active ? 'User deactivated' : 'User activated')
      } else {
        const e = await r.json().catch(() => ({ detail: 'Unknown error' }))
        const msg = Array.isArray(e.detail) ? e.detail.map((d: any) => d.msg || d).join(', ') : (e.detail || 'Action failed')
        addToast('error', msg)
      }
    } catch { addToast('error', 'Failed to update user status') }
  }

  const openEdit = (u: User) => {
    setEditTarget(u)
    setEditForm({ full_name: u.full_name || '', email: u.email, role_name: u.roles[0] || 'VIEWER' })
    setShowEditModal(true)
  }

  /* ---------- derived ---------- */

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (u.full_name || '').toLowerCase().includes(searchQuery.toLowerCase())
  )

  const activeUsers = users.filter(u => u.is_active)
  const ownerCount = users.filter(u => u.roles.includes('OWNER')).length

  /* ---------- guards ---------- */

  if (!canManageUsers()) {
    return (
      <div className="p-8"><div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">You do not have permission to manage users. Required: OWNER or ADMIN role.</p>
      </div></div>
    )
  }
  if (loading) {
    return <div className="p-8 flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" /></div>
  }

  /* ---------- role badge ---------- */
  const RoleBadge = ({ role }: { role: string }) => {
    const m = ROLE_META[role] || ROLE_META.VIEWER
    const Icon = m.icon
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${m.bg} ${m.color}`}>
        <Icon className="h-3 w-3" />{m.label}
      </span>
    )
  }

  /* ================================================================== */
  /*  RENDER                                                             */
  /* ================================================================== */

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">

      {/* ---- header ---- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <UsersIcon className="h-7 w-7 text-blue-600" />User Management
          </h1>
          <p className="mt-1 text-sm text-gray-500">Manage platform users, roles, and access &mdash; synced with Keycloak</p>
        </div>
        <button onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium shadow-sm transition">
          <UserPlus className="h-4 w-4" />Create User
        </button>
      </div>

      {/* ---- stats ---- */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Active', value: activeUsers.length, accent: 'text-blue-600' },
          { label: 'Owners', value: ownerCount, accent: 'text-amber-600' },
          { label: 'Admins', value: users.filter(u => u.roles.includes('ADMIN')).length, accent: 'text-indigo-600' },
          { label: 'Operators / Viewers', value: users.filter(u => (u.roles.includes('OPERATOR') || u.roles.includes('VIEWER'))).length, accent: 'text-emerald-600' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.accent}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* ---- toolbar ---- */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input type="text" placeholder="Search by name, email, or username..." value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
        </div>
      </div>

      {/* ---- table ---- */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50/80">
              <tr>
                {['User','Email','Role','Status','Last Login',''].map((h, i) => (
                  <th key={h||i} className={`px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider ${i === 5 ? 'text-right' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-10 text-center text-sm text-gray-400">No users found</td></tr>
              )}
              {filtered.map(user => (
                <tr key={user.id} className="group transition hover:bg-gray-50/70">
                  {/* avatar + name */}
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className={`h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold ${
                        user.roles.includes('OWNER') ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                      }`}>{user.username[0].toUpperCase()}</div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 leading-tight">{user.username}</p>
                        {user.full_name && <p className="text-xs text-gray-500">{user.full_name}</p>}
                      </div>
                    </div>
                  </td>
                  {/* email */}
                  <td className="px-5 py-3.5 text-sm text-gray-600">{user.email}</td>
                  {/* role */}
                  <td className="px-5 py-3.5"><div className="flex gap-1 flex-wrap">{user.roles.map(r => <RoleBadge key={r} role={r} />)}</div></td>
                  {/* status */}
                  <td className="px-5 py-3.5">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700"><CheckCircle className="h-3 w-3" />Active</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600"><XCircle className="h-3 w-3" />Inactive</span>
                    )}
                  </td>
                  {/* last login */}
                  <td className="px-5 py-3.5 text-sm text-gray-500">{user.last_login ? new Date(user.last_login).toLocaleDateString() : <span className="text-gray-300">Never</span>}</td>
                  {/* actions */}
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1 opacity-60 group-hover:opacity-100 transition">
                      <button onClick={() => openEdit(user)} title="Edit user"
                        className="p-1.5 rounded-md hover:bg-blue-50 text-gray-500 hover:text-blue-600 transition"><Pencil className="h-4 w-4" /></button>
                      <button onClick={() => toggleActive(user.id, user.is_active)} title={user.is_active ? 'Deactivate' : 'Activate'}
                        className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition">
                        {user.is_active ? <XCircle className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                      </button>
                      <button onClick={() => { setPwUserId(user.id); setShowResetPwModal(true) }} title="Reset password"
                        className="p-1.5 rounded-md hover:bg-orange-50 text-gray-500 hover:text-orange-600 transition"><Key className="h-4 w-4" /></button>
                      <button onClick={() => { setDeleteTarget({ id: user.id, username: user.username }); setShowDeleteModal(true) }} title="Delete user"
                        className="p-1.5 rounded-md hover:bg-red-50 text-gray-500 hover:text-red-600 transition"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ---- role legend ---- */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Role Definitions</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {Object.entries(ROLE_META).map(([key, m]) => {
            const Icon = m.icon
            return (
              <div key={key} className={`flex items-start gap-2.5 p-3 rounded-lg border ${m.bg}`}>
                <Icon className={`h-4 w-4 mt-0.5 ${m.color}`} />
                <div>
                  <p className={`text-sm font-semibold ${m.color}`}>{m.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ================================================================== */}
      {/*  MODALS                                                             */}
      {/* ================================================================== */}

      {/* ---- CREATE ---- */}
      {showCreateModal && (
        <Modal onClose={() => setShowCreateModal(false)} title="Create New User">
          <div className="space-y-4">
            <Field label="Username *">
              <input type="text" value={newUser.username} onChange={e => setNewUser({...newUser, username: e.target.value})}
                className="input" placeholder="johndoe" />
            </Field>
            <Field label="Email *">
              <input type="email" value={newUser.email} onChange={e => setNewUser({...newUser, email: e.target.value})}
                className="input" placeholder="john@example.com" />
            </Field>
            <Field label="Full Name">
              <input type="text" value={newUser.full_name} onChange={e => setNewUser({...newUser, full_name: e.target.value})}
                className="input" placeholder="John Doe" />
            </Field>
            <Field label="Password *">
              <input type="password" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})}
                className="input" placeholder="Secure password" />
              <p className="text-xs text-gray-500 mt-1">Min 8 chars, 1 upper, 1 lower, 1 digit. User must change on first login.</p>
            </Field>
            <Field label="Role *">
              <select value={newUser.role_names[0]} onChange={e => setNewUser({...newUser, role_names: [e.target.value]})} className="input">
                {availableRoles.filter(r => r.assignable).map(r => (
                  <option key={r.name} value={r.name}>
                    {(ROLE_META[r.name]?.label || r.name)} {'\u2014'} {r.description}
                  </option>
                ))}
                {availableRoles.length === 0 && <>
                  <option value="VIEWER">Viewer</option>
                  <option value="OPERATOR">Operator</option>
                  <option value="ADMIN">Admin</option>
                  {isOwner() && <option value="OWNER">Owner</option>}
                </>}
              </select>
            </Field>
          </div>
          <ModalFooter>
            <button onClick={createUser} disabled={actionLoading} className="btn-primary flex-1">{actionLoading ? 'Creating...' : 'Create User'}</button>
            <button onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">Cancel</button>
          </ModalFooter>
        </Modal>
      )}

      {/* ---- EDIT ---- */}
      {showEditModal && editTarget && (
        <Modal onClose={() => { setShowEditModal(false); setEditTarget(null) }} title={`Edit User: ${editTarget.username}`}>
          <div className="space-y-4">
            <Field label="Full Name">
              <input type="text" value={editForm.full_name} onChange={e => setEditForm({...editForm, full_name: e.target.value})} className="input" />
            </Field>
            <Field label="Email">
              <input type="email" value={editForm.email} onChange={e => setEditForm({...editForm, email: e.target.value})} className="input" />
            </Field>
            <Field label="Role">
              <select value={editForm.role_name} onChange={e => setEditForm({...editForm, role_name: e.target.value})} className="input">
                {availableRoles.filter(r => r.assignable).map(r => (
                  <option key={r.name} value={r.name}>{(ROLE_META[r.name]?.label || r.name)} {'\u2014'} {r.description}</option>
                ))}
                {availableRoles.length === 0 && <>
                  <option value="VIEWER">Viewer</option>
                  <option value="OPERATOR">Operator</option>
                  <option value="ADMIN">Admin</option>
                  {isOwner() && <option value="OWNER">Owner</option>}
                </>}
              </select>
              {editForm.role_name !== editTarget.roles[0] && (
                <p className="text-xs text-amber-600 mt-1 font-medium">Role will change from {editTarget.roles[0]} to {editForm.role_name}</p>
              )}
            </Field>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-700">Changes will be synced to Keycloak automatically.</p>
            </div>
          </div>
          <ModalFooter>
            <button onClick={saveEdit} disabled={actionLoading} className="btn-primary flex-1">{actionLoading ? 'Saving...' : 'Save Changes'}</button>
            <button onClick={() => { setShowEditModal(false); setEditTarget(null) }} className="btn-secondary flex-1">Cancel</button>
          </ModalFooter>
        </Modal>
      )}

      {/* ---- USER CREATED RESULT ---- */}
      {showCreatedResult && (
        <Modal onClose={() => setShowCreatedResult(null)} title="User Created Successfully" icon={<CheckCircle className="text-green-600" size={24} />}>
          {showCreatedResult.welcome_email_sent ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">Welcome email with credentials sent to <strong>{showCreatedResult.email}</strong>. User must change password on first login.</p>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2"><AlertTriangle className="text-amber-600 shrink-0" size={18} /><span className="font-medium text-amber-800 text-sm">User created in Keycloak</span></div>
              <p className="text-xs text-amber-700">SMTP unavailable &mdash; share credentials securely with the user. The temporary password was set in Keycloak and must be changed on first login.</p>
              <div className="bg-white border border-gray-200 rounded p-3 font-mono text-sm space-y-1">
                <div><span className="text-gray-400">Username:</span> <strong>{showCreatedResult.username}</strong></div>
                <div><span className="text-gray-400">Email:</span> <strong>{showCreatedResult.email}</strong></div>
                <div><span className="text-gray-400">Password:</span> <em className="text-gray-500">Set during creation &mdash; share securely</em></div>
              </div>
            </div>
          )}
          <ModalFooter><button onClick={() => setShowCreatedResult(null)} className="btn-secondary w-full">Close</button></ModalFooter>
        </Modal>
      )}

      {/* ---- DELETE CONFIRM ---- */}
      {showDeleteModal && deleteTarget && (
        <Modal onClose={() => { setShowDeleteModal(false); setDeleteTarget(null) }} title="Delete User"
          icon={<div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center"><AlertTriangle className="h-5 w-5 text-red-600" /></div>}>
          <p className="text-gray-600 text-sm">Are you sure you want to <strong>permanently delete</strong> <strong>{deleteTarget.username}</strong>?</p>
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mt-3">
            <p className="text-xs text-red-700 font-medium">This action is irreversible. The user will be removed from:</p>
            <ul className="text-xs text-red-600 mt-1 ml-4 list-disc">
              <li>Keycloak (authentication)</li>
              <li>Local database (roles &amp; metadata)</li>
              <li>All active sessions will be terminated</li>
            </ul>
          </div>
          <ModalFooter>
            <button onClick={() => { setShowDeleteModal(false); setDeleteTarget(null) }} className="btn-secondary" disabled={actionLoading}>Cancel</button>
            <button onClick={confirmDelete} className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm font-medium disabled:opacity-50" disabled={actionLoading}>
              {actionLoading ? 'Deleting...' : 'Delete Permanently'}
            </button>
          </ModalFooter>
        </Modal>
      )}

      {/* ---- RESET PASSWORD ---- */}
      {showResetPwModal && (
        <Modal onClose={() => { setShowResetPwModal(false); setPwUserId(null); setNewPassword('') }} title="Reset Password (Keycloak)">
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-700">Password will be reset directly in Keycloak. Choose one option:</p>
            </div>

            {/* Option 1: Send email */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2"><Mail className="h-4 w-4" />Send Reset Email</h4>
              <p className="text-xs text-gray-500 mt-1">Keycloak will send a password reset link to the user's email. Requires SMTP configured in Keycloak.</p>
              <button onClick={sendResetEmail} disabled={actionLoading}
                className="mt-2 w-full bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50 transition">
                {actionLoading ? 'Sending...' : 'Send Reset Email'}
              </button>
            </div>

            {/* Option 2: Set temp password */}
            <div className="border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 flex items-center gap-2"><Key className="h-4 w-4" />Set Temporary Password</h4>
              <p className="text-xs text-gray-500 mt-1">Set a new temporary password. User must change it on next login.</p>
              <Field label="New Password *">
                <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="input" placeholder="Secure password" />
                <p className="text-xs text-gray-500 mt-1">Min 8 chars, 1 upper, 1 lower, 1 digit</p>
              </Field>
              <button onClick={resetPassword} disabled={actionLoading || !newPassword}
                className="mt-2 w-full bg-orange-600 text-white px-3 py-2 rounded-lg hover:bg-orange-700 text-sm font-medium disabled:opacity-50 transition">
                {actionLoading ? 'Resetting...' : 'Set Temporary Password'}
              </button>
            </div>
          </div>
          <ModalFooter>
            <button onClick={() => { setShowResetPwModal(false); setPwUserId(null); setNewPassword('') }} className="btn-secondary w-full">Cancel</button>
          </ModalFooter>
        </Modal>
      )}

      {/* ---- TOASTS ---- */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(t => (
          <div key={t.id} className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
            t.type === 'success' ? 'bg-green-600 text-white' : t.type === 'error' ? 'bg-red-600 text-white' : 'bg-blue-600 text-white'
          }`}>
            {t.type === 'success' && <CheckCircle className="h-4 w-4" />}
            {t.type === 'error' && <XCircle className="h-4 w-4" />}
            {t.message}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Shared UI primitives                                               */
/* ------------------------------------------------------------------ */

function Modal({ children, onClose, title, icon }: { children: React.ReactNode; onClose: () => void; title: string; icon?: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden max-h-[90vh] overflow-y-auto">
        <div className="px-6 pt-5 pb-3 flex items-center gap-3">
          {icon}{icon ? null : null}
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="px-6 pb-2">{children}</div>
      </div>
    </div>
  )
}

function ModalFooter({ children }: { children: React.ReactNode }) {
  return <div className="flex gap-3 mt-5 pb-5">{children}</div>
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  )
}
