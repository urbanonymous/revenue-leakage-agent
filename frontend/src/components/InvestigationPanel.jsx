import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { investigateAll, investigateCustomer } from '../api/investigation'
import { Search, Loader2 } from 'lucide-react'

const CUSTOMERS = [
  'Sopita',
  'Pelota',
  'Telefon Inc',
  'Hooli Corp',
]

function InvestigationPanel({ onInvestigationComplete }) {
  const [error, setError] = useState(null)
  const [investigationType, setInvestigationType] = useState('full') // 'full' or 'specific'
  const [selectedCustomer, setSelectedCustomer] = useState('')

  const investigationMutation = useMutation({
    mutationFn: async () => {
      if (investigationType === 'full') {
        return investigateAll()
      } else {
        if (!selectedCustomer) {
          throw new Error('Please select a customer')
        }
        return investigateCustomer(selectedCustomer)
      }
    },
    onSuccess: (data) => {
      setError(null)
      onInvestigationComplete(data)
    },
    onError: (error) => {
      setError(error.message || 'Failed to run investigation')
    },
  })

  const handleInvestigate = () => {
    investigationMutation.mutate()
  }

  const isDisabled = investigationMutation.isPending || 
    (investigationType === 'specific' && !selectedCustomer)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Run Investigation</h2>
      
      {/* Investigation Type Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Investigation Scope
        </label>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="full"
              checked={investigationType === 'full'}
              onChange={(e) => setInvestigationType(e.target.value)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              disabled={investigationMutation.isPending}
            />
            <span className="ml-2 text-sm text-gray-700">Full Investigation (All Customers)</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="specific"
              checked={investigationType === 'specific'}
              onChange={(e) => setInvestigationType(e.target.value)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              disabled={investigationMutation.isPending}
            />
            <span className="ml-2 text-sm text-gray-700">Specific Customer</span>
          </label>
        </div>
      </div>

      {/* Customer Selector (only shown for specific investigation) */}
      {investigationType === 'specific' && (
        <div className="mb-4">
          <label htmlFor="customer" className="block text-sm font-medium text-gray-700 mb-2">
            Select Customer
          </label>
          <select
            id="customer"
            value={selectedCustomer}
            onChange={(e) => setSelectedCustomer(e.target.value)}
            disabled={investigationMutation.isPending}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            <option value="">-- Select a customer --</option>
            {CUSTOMERS.map((customer) => (
              <option key={customer} value={customer}>
                {customer}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Run Button */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          {investigationType === 'full' 
            ? 'Analyze all billing plans and invoices to detect revenue leakage'
            : selectedCustomer 
              ? `Investigate revenue issues for ${selectedCustomer}`
              : 'Select a customer to investigate'}
        </p>
        <button
          onClick={handleInvestigate}
          disabled={isDisabled}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {investigationMutation.isPending ? (
            <>
              <Loader2 className="animate-spin h-5 w-5 mr-2" />
              Investigating...
            </>
          ) : (
            <>
              <Search className="h-5 w-5 mr-2" />
              Run Investigation
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {investigationMutation.isSuccess && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-md p-4">
          <p className="text-sm text-green-800">
            Investigation completed successfully!
          </p>
        </div>
      )}
    </div>
  )
}

export default InvestigationPanel

