import SupportForm from '@/components/SupportForm'

export default function Home() {
  return (
    <main className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">FlowBoard Support</h1>
        <p className="mt-2 text-gray-600">We&apos;re here to help. Submit your request and our AI assistant will respond shortly.</p>
      </div>
      <SupportForm apiEndpoint={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/support/submit'} />
    </main>
  )
}
