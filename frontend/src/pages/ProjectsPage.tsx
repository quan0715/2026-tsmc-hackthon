import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getProjectsAPI } from '@/services/project.service'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Project } from '@/types/project.types'

const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  CREATED: 'secondary',
  PROVISIONING: 'warning',
  READY: 'success',
  RUNNING: 'default',
  STOPPED: 'secondary',
  FAILED: 'destructive',
}

export default function ProjectsPage() {
  const { user, logout } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await getProjectsAPI()
      setProjects(data.projects)
    } catch (error) {
      console.error('載入專案失敗', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">載入中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">AI 舊程式碼智能重構系統</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.username} ({user?.email})
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              登出
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto p-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold">我的專案</h2>
          <Link to="/projects/new">
            <Button>+ 建立專案</Button>
          </Link>
        </div>

        {projects.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <p className="text-gray-600 mb-4">尚無專案</p>
              <Link to="/projects/new">
                <Button>建立第一個專案</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate" title={project.repo_url}>
                          {project.repo_url.split('/').pop()?.replace('.git', '') || project.repo_url}
                        </h3>
                        <p className="text-xs text-gray-500 truncate">{project.repo_url}</p>
                      </div>
                      <Badge variant={statusColors[project.status]}>
                        {project.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                      {project.init_prompt}
                    </p>
                    <div className="text-xs text-gray-500">
                      <div>分支: {project.branch}</div>
                      <div>建立於: {new Date(project.created_at).toLocaleString('zh-TW')}</div>
                    </div>
                    {project.last_error && (
                      <div className="mt-2 text-xs text-red-500 bg-red-50 p-2 rounded">
                        錯誤: {project.last_error}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
