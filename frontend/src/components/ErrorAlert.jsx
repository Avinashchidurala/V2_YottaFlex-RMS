import { ExclamationCircleIcon } from '@heroicons/react/24/outline'

export default function ErrorAlert({ message }) {
  return (
    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
      <ExclamationCircleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-sm font-medium text-red-700">Error</p>
        <p className="text-sm text-red-600 mt-0.5">{message || 'An unexpected error occurred.'}</p>
      </div>
    </div>
  )
}
