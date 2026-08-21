import React, { useEffect, useState } from 'react';
import { Building2, Plus, Trash2 } from 'lucide-react';
import { departmentsApi } from '../api/endpoints';
import type { Department } from '../types';
import { Modal } from '../components/UI/Modal';

export const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [name, setName] = useState<string>('');
  const [code, setCode] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      const data = await departmentsApi.list();
      setDepartments(data);
    } catch (err) {
      console.error('Failed to load departments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setSubmitting(true);
    try {
      await departmentsApi.create({ name, code, description });
      setIsModalOpen(false);
      setName('');
      setCode('');
      setDescription('');
      fetchDepartments();
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to create department.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this department?')) return;
    try {
      await departmentsApi.delete(id);
      fetchDepartments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete department.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Departments</h1>
          <p className="page-subtitle">Organizational structure, business units, and department codes</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <Plus size={18} />
          <span>New Department</span>
        </button>
      </div>

      {/* Grid of Department Cards */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading departments...
        </div>
      ) : departments.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No departments created yet. Click "New Department" to get started.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
          {departments.map((dept) => (
            <div key={dept.id} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: 'rgba(6, 182, 212, 0.15)',
                      color: 'var(--accent-cyan)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Building2 size={20} />
                    </div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>{dept.name}</h3>
                  </div>
                  <span className="badge badge-info">{dept.code}</span>
                </div>

                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5, marginTop: '8px' }}>
                  {dept.description || 'No description provided for this department.'}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  ID: {dept.id.substring(0, 8)}...
                </span>
                <button
                  onClick={() => handleDelete(dept.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-rose)',
                    cursor: 'pointer',
                    padding: '4px',
                    borderRadius: '6px'
                  }}
                  title="Delete department"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Department">
        {modalError && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(244,63,94,0.15)', color: 'var(--accent-rose)', marginBottom: '16px', fontSize: '0.8125rem' }}>
            {modalError}
          </div>
        )}
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label className="input-label">Department Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Engineering"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Department Code</label>
            <input
              type="text"
              required
              placeholder="e.g. ENG"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Description</label>
            <textarea
              rows={3}
              placeholder="Brief description of responsibilities..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field"
              style={{ resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '12px' }}>
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? 'Creating...' : 'Create Department'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
