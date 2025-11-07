import { useState } from 'react'
import { AlertCircle, AlertTriangle, Info, ChevronDown, ChevronRight } from 'lucide-react'

function FindingsTable({ findings = [] }) {
  const [expandedRows, setExpandedRows] = useState(new Set())

  const toggleRow = (findingId) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(findingId)) {
      newExpanded.delete(findingId)
    } else {
      newExpanded.add(findingId)
    }
    setExpandedRows(newExpanded)
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />
      default:
        return null
    }
  }

  const getSeverityBadge = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800',
      warning: 'bg-yellow-100 text-yellow-800',
      info: 'bg-blue-100 text-blue-800',
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[severity]}`}>
        {severity.toUpperCase()}
      </span>
    )
  }

  const getIssueTypeLabel = (issueType) => {
    const labels = {
      missing_invoice: 'Missing Invoice',
      underbilling: 'Underbilling',
      overbilling: 'Overbilling',
      currency_mismatch: 'Currency Mismatch',
      orphan_invoice: 'Orphan Invoice',
      amendment_issue: 'Amendment Issue',
    }
    return labels[issueType] || issueType
  }

  if (findings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Findings</h2>
        <p className="text-gray-500 text-center py-8">
          No findings to display. Run an investigation to detect revenue leakage.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Findings ({findings.length})
        </h2>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-8"></th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Customer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Issue Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Expected
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actual
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Impact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {findings.map((finding) => {
              const isExpanded = expandedRows.has(finding.finding_id)
              return (
                <>
                  <tr
                    key={finding.finding_id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => toggleRow(finding.finding_id)}
                  >
                    <td className="px-6 py-4">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {finding.customer_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getIssueTypeLabel(finding.issue_type)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {finding.expected || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {finding.actual || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${finding.impact_amount.toLocaleString()} {finding.impact_currency}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getSeverityBadge(finding.severity)}
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td colSpan="7" className="px-6 py-4 bg-gray-50">
                        <div className="space-y-2">
                          <div>
                            <span className="text-xs font-medium text-gray-500">Description:</span>
                            <p className="text-sm text-gray-900 mt-1">{finding.description}</p>
                          </div>
                          <div>
                            <span className="text-xs font-medium text-gray-500">Evidence:</span>
                            <p className="text-sm text-gray-700 mt-1">{finding.evidence}</p>
                          </div>
                          <div className="text-xs text-gray-500">
                            Plan ID: {finding.plan_id} | Finding ID: {finding.finding_id}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default FindingsTable

