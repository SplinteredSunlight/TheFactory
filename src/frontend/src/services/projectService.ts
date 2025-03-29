import { api } from './api';

export interface ProjectProgress {
  projectId: string;
  progress: number;
  completedTasks: number;
  totalTasks: number;
  status: 'on_track' | 'at_risk' | 'delayed' | 'completed';
  estimatedCompletion: string | null;
  lastUpdated: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  startDate: string;
  endDate: string | null;
  status: 'active' | 'completed' | 'on_hold' | 'cancelled';
  owner: string;
  team: string[];
  createdAt: string;
  updatedAt: string;
}

// Extend the base API with project-related endpoints
export const projectApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getProjects: builder.query<Project[], void>({
      query: () => '/projects',
      providesTags: ['Projects'],
    }),
    
    getProject: builder.query<Project, string>({
      query: (projectId) => `/projects/${projectId}`,
      providesTags: (result, error, projectId) => [{ type: 'Projects', id: projectId }],
    }),
    
    getProjectProgress: builder.query<ProjectProgress, string>({
      query: (projectId) => `/projects/${projectId}/progress`,
      providesTags: (result, error, projectId) => [
        { type: 'Projects', id: projectId },
        'ProjectProgress',
      ],
    }),
    
    createProject: builder.mutation<Project, Partial<Project>>({
      query: (project) => ({
        url: '/projects',
        method: 'POST',
        body: project,
      }),
      invalidatesTags: ['Projects'],
    }),
    
    updateProject: builder.mutation<Project, { id: string; project: Partial<Project> }>({
      query: ({ id, project }) => ({
        url: `/projects/${id}`,
        method: 'PATCH',
        body: project,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Projects', id },
        'Projects',
      ],
    }),
    
    deleteProject: builder.mutation<void, string>({
      query: (id) => ({
        url: `/projects/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Projects'],
    }),
    
    updateProjectProgress: builder.mutation<ProjectProgress, { projectId: string; progress: Partial<ProjectProgress> }>({
      query: ({ projectId, progress }) => ({
        url: `/projects/${projectId}/progress`,
        method: 'PATCH',
        body: progress,
      }),
      invalidatesTags: (result, error, { projectId }) => [
        { type: 'Projects', id: projectId },
        'ProjectProgress',
      ],
    }),
  }),
});

// Export hooks for usage in components
export const {
  useGetProjectsQuery,
  useGetProjectQuery,
  useGetProjectProgressQuery,
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useDeleteProjectMutation,
  useUpdateProjectProgressMutation,
} = projectApi;
