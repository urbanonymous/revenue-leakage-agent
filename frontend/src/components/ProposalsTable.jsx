import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applyProposal, getProposals, getSandboxActions } from '../api/proposals'
import { CheckCircle, XCircle, Loader2, FileText } from 'lucide-react'

function ProposalsTable({ proposals = [], showApplied = false }) {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(null)

  // Fetch sandbox proposals if showApplied is true
  const { data: sandboxData } = useQuery({
    queryKey: ['sandbox-actions'],
    queryFn: getSandboxActions,
    enabled: showApplied,
  })

  const applyMutation = useMutation({
    mutationFn: applyProposal,
    onSuccess: () => {
      queryClient.invalidateQueries(['sandbox-actions'])
      setShowModal(null)
    },
  })

  const displayProposals = showApplied && sandboxData
    ? [
        ...(sandboxData.make_good_invoices || []).map(mg => ({
          proposal_id: mg.proposal_id,
          proposal_type: 'make_good_invoice',
          customer_name: mg.customer_name,
          amount: mg.amount,
          currency: mg.currency,
          reason: mg.reason,
          status: 'applied',
        })),
        ...(sandboxData.credit_memos || []).map(cm => ({
          proposal_id: cm.proposal_id,
          proposal_type: 'credit_memo',
          customer_name: 'N/A',
          amount: cm.amount,
          currency: cm.currency,
          reason: cm.reason,
          status: 'applied',
        })),
      ]
    : proposals

  const getTypeLabel = (type) => {
    const labels = {
      make_good_invoice: 'Make-Good Invoice',
      credit_memo: 'Credit Memo',
      plan_amendment: 'Plan Amendment',
    }
    return labels[type] || type
  }

  const getStatusBadge = (status) => {
    if (status === 'applied') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Applied
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
        Pending
      </span>
    )
  }

  if (displayProposals.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Proposals</h2>
        <p className="text-gray-500 text-center py-8">No proposals available.</p>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Proposals ({displayProposals.length})
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayProposals.map((proposal) => (
                <tr key={proposal.proposal_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {getTypeLabel(proposal.proposal_type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {proposal.customer_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {proposal.amount ? `$${proposal.amount.toLocaleString()} ${proposal.currency}` : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {proposal.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(proposal.status)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {proposal.status === 'pending' && (
                      <button
                        onClick={() => setShowModal(proposal)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Apply
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Apply Proposal</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to apply this {getTypeLabel(showModal.proposal_type).toLowerCase()}?
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowModal(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => applyMutation.mutate(showModal)}
                disabled={applyMutation.isPending}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
              >
                {applyMutation.isPending ? 'Applying...' : 'Apply'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default ProposalsTable

