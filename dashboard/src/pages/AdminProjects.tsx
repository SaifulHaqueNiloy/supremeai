// AdminProjects.tsx - Project Management Page (Modularized)

import React, { useState, useEffect } from 'react';
import { Card, message, Spin, Alert } from 'antd';
import AdminLayout from '../components/AdminLayout';
import { authUtils } from '../lib/authUtils';

// Import Modular Components
import { Project, GenerationForm, GenerationStatus } from '../components/projects/types';
import ProjectTable from '../components/projects/ProjectTable';
import ProjectModal from '../components/projects/ProjectModal';
import AppGenerationCard from '../components/projects/AppGenerationCard';
import ProjectActionToolbar from '../components/projects/ProjectActionToolbar';

const AdminProjects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  
  // App Generation State
  const [generationForm, setGenerationForm] = useState<GenerationForm>({
    name: '',
    description: '',
    platform: 'fullstack',
    database: 'PostgreSQL',
    useAI: true
  });
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus>('idle');
  const [generationStep, setGenerationStep] = useState(0);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationResult, setGenerationResult] = useState<any>(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authUtils.fetchWithAuth('/api/projects');
      if (!response.ok) throw new Error('Failed to fetch projects');
      const result = await response.json();
      setProjects(result.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
      message.error('Error fetching projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateOrUpdate = async (values: any) => {
    try {
      const isEdit = !!editingProject;
      const url = isEdit ? `/api/projects/${editingProject.id}` : '/api/projects';
      const method = isEdit ? 'PUT' : 'POST';
      
      const response = await authUtils.fetchWithAuth(url, {
        method,
        body: JSON.stringify(values),
      });
      
      if (!response.ok) throw new Error(`Failed to ${isEdit ? 'update' : 'create'} project`);
      
      message.success(`Project ${isEdit ? 'updated' : 'created'} successfully`);
      setModalVisible(false);
      fetchProjects();
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Operation failed');
    }
  };

  const handleUpdateStatus = async (id: string, status: string) => {
    try {
      const response = await authUtils.fetchWithAuth(`/api/projects/${id}/status?status=${encodeURIComponent(status)}`, {
        method: 'PUT',
      });
      if (!response.ok) throw new Error('Failed to update status');
      message.success('Status updated');
      fetchProjects();
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Failed to update');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await authUtils.fetchWithAuth(`/api/projects/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete project');
      message.success('Project deleted');
      fetchProjects();
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const handleGenerateApp = async () => {
    if (!generationForm.name || !generationForm.description) {
      message.warning('Please provide both name and description');
      return;
    }

    setGenerationStatus('generating');
    setGenerationStep(0);
    setGenerationProgress(10);
    
    try {
      // Simulation of Pipeline Steps
      // Step 1: Analyze requirements
      setGenerationStep(1);
      setGenerationProgress(25);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Step 2: Design architecture
      setGenerationStep(2);
      setGenerationProgress(50);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Step 3: Generate code (Actual API Call)
      setGenerationStep(3);
      setGenerationProgress(75);
      
      const response = await authUtils.fetchWithAuth('/api/generate', {
        method: 'POST',
        body: JSON.stringify({
          ...generationForm,
          type: 'project',
        }),
      });
      
      if (!response.ok) throw new Error('Generation engine failed');
      
      const result = await response.json();
      
      // Step 4: Finalize
      setGenerationStep(4);
      setGenerationProgress(100);
      setGenerationStatus('success');
      setGenerationResult(result);
      
      // Sync local project list
      fetchProjects();
      message.success('Application generation pipeline completed successfully');
    } catch (err) {
      setGenerationStatus('error');
      message.error(err instanceof Error ? err.message : 'Generation pipeline failed');
    }
  };

  return (
    <AdminLayout title="System Orchestrator: Projects">
      <Card className="glass-card">
        <ProjectActionToolbar 
          onNewProject={() => {
            setEditingProject(null);
            setModalVisible(true);
          }}
          onRefresh={fetchProjects}
          loading={loading}
        />

        {error && (
          <Alert 
            type="error" 
            message="System Sync Error" 
            description={error} 
            showIcon 
            style={{ marginBottom: 16 }}
            action={<button onClick={fetchProjects} className="retry-btn">Retry Sync</button>} 
          />
        )}

        {loading && !projects.length ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="Synchronizing Project Vault..." />
          </div>
        ) : (
          <ProjectTable 
            projects={projects}
            loading={loading}
            onEdit={(project) => {
              setEditingProject(project);
              setModalVisible(true);
            }}
            onDelete={handleDelete}
            onUpdateStatus={handleUpdateStatus}
          />
        )}
      </Card>

      <AppGenerationCard 
        generationForm={generationForm}
        setGenerationForm={setGenerationForm}
        generationStatus={generationStatus}
        generationStep={generationStep}
        generationProgress={generationProgress}
        generationResult={generationResult}
        onGenerate={handleGenerateApp}
      />

      <ProjectModal 
        visible={modalVisible}
        editingProject={editingProject}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleCreateOrUpdate}
      />
    </AdminLayout>
  );
};

export default AdminProjects;
