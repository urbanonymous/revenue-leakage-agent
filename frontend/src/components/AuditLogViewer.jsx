import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAuditLog, rollbackAction } from '../api/proposals'
import { History, RotateCcw, CheckCircle, XCircle } from 'lucide-react'

function AuditLogViewer() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['audit-log'],
    queryFn: () => getAuditLog(50),
  })

  const rollbackMutation = useMutation({
    mutationFn: rollbackAction,
    onSuccess: () => {
      queryClient.invalidateQueries(['audit-log'])
      queryClient.invalidateQueries(['sandbox-actions'])
    },
  })

  const auditLog = data?.audit_log || []

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString()
  }

  const getActionIcon = (actionType) => {
    if (actionType === 'apply') {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    }
    return <XCircle className="h-5 w-5 text-red-500" />
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-center text-gray-500">Loading audit log...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <History className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Audit Log</h2>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          Complete history of all actions and rollbacks
        </p>
      </div>

      {auditLog.length === 0 ? (
        <div className="p-6">
          <p className="text-center text-gray-500">No actions recorded yet</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {auditLog.map((entry) => (
                <tr key={entry.action_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getActionIcon(entry.action_type)}
                      <span className="text-sm font-medium text-gray-900">
                        {entry.action_type.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.proposal_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.customer_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.amount ? `$${entry.amount.toLocaleString()} ${entry.currency}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(entry.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    {entry.action_type === 'apply' && (
                      <button
                        onClick={() => rollbackMutation.mutate(entry.action_id)}
                        disabled={rollbackMutation.isPending}
                        className="text-red-600 hover:text-red-900 inline-flex items-center space-x-1"
                      >
                        <RotateCcw className="h-4 w-4" />
                        <span>Rollback</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default AuditLogViewer

