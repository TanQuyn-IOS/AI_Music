import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('App error boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#060713] text-white px-6">
          <div className="max-w-md w-full rounded-3xl border border-red-500/30 bg-white/[0.03] p-8 text-center shadow-2xl">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 text-3xl">
              ⚠️
            </div>
            <h2 className="text-2xl font-black mb-2">Có lỗi xảy ra</h2>
            <p className="text-sm text-white/60 mb-5">
              Ứng dụng đã gặp sự cố. Vui lòng tải lại trang hoặc quay lại sau.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="rounded-2xl bg-gradient-to-r from-indigo-500 to-cyan-500 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
            >
              Tải lại trang
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
