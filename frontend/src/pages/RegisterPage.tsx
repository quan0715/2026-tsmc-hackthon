import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { registerAPI } from '@/services/auth.service'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ReforgeLogo } from '@/components/brand/ReforgeLogo'
import { apiErrorMessage } from '@/utils/apiError'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 前端驗證
    if (!email.includes('@')) {
      setError('請輸入有效的 Email 地址')
      return
    }

    if (username.length < 3) {
      setError('使用者名稱必須至少 3 個字元')
      return
    }

    if (password.length < 8) {
      setError('密碼必須至少 8 個字元')
      return
    }

    setLoading(true)

    try {
      await registerAPI({ email, username, password })

      // 註冊成功，自動登入（使用 username）
      await login(username, password)

      navigate('/projects')
    } catch (err: any) {
      // 詳細的錯誤處理
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 400 || status === 422) {
        if (detail?.includes('email') || detail?.includes('Email')) {
          setError('Email 已被使用或格式不正確')
        } else if (detail?.includes('username') || detail?.includes('Username')) {
          setError('使用者名稱已被使用或格式不正確')
        } else if (detail?.includes('password') || detail?.includes('Password')) {
          setError('密碼格式不正確（必須至少 8 個字元）')
        } else {
          setError(detail || '輸入格式不正確，請檢查所有欄位')
        }
      } else if (status === 500) {
        setError('伺服器錯誤，請稍後再試')
      } else if (err.code === 'ERR_NETWORK') {
        setError('無法連線到伺服器，請檢查網路連線')
      } else {
        setError(apiErrorMessage(err, '註冊失敗，請重試'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-gradient">
      <Card className="w-full max-w-md backdrop-blur-sm bg-card/80 border-border">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <ReforgeLogo size="lg" />
          </div>
          <CardTitle className="text-center">
            <span className="text-brand-gradient">註冊新帳號</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-900/30 border border-red-700/50 text-red-400 p-4 rounded-lg flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <div className="flex-1">
                  <div className="font-semibold mb-1">註冊失敗</div>
                  <div className="text-sm">{error}</div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="your@email.com"
              />
              <p className="text-xs text-muted-foreground mt-1">必須是有效的 Email 格式</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">使用者名稱</label>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={3}
                placeholder="username"
              />
              <p className="text-xs text-muted-foreground mt-1">至少 3 個字元，最多 50 個字元</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-foreground">密碼</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="至少 8 個字元"
              />
              <p className="text-xs text-muted-foreground mt-1">至少 8 個字元，最多 100 個字元</p>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? '註冊中...' : '註冊'}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              已有帳號？{' '}
              <Link to="/login" className="text-brand-blue-400 hover:underline">
                登入
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
