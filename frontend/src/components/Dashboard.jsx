import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import InvestigationPanel from './InvestigationPanel'
import FindingsTable from './FindingsTable'
import ProposalsTable from './ProposalsTable'
import ChatInterface from './ChatInterface'
import AuditLogViewer from './AuditLogViewer'
import { getProposals } from '../api/proposals'
import { BarChart3, AlertTriangle, FileText, MessageSquare, History } from 'lucide-react'

function Dashboard() {
  const [activeTab, setActiveTab] = useState('investigation')
  const [investigationResults, setInvestigationResults] = useState(null)

  // Fetch proposals for the Proposals tab
  const { data: proposalsData } = useQuery({
    queryKey: ['proposals'],
    queryFn: getProposals,
    enabled: activeTab === 'proposals', // Only fetch when on Proposals tab
  })

  const tabs = [
    { id: 'investigation', name: 'Investigation', icon: BarChart3 },
    { id: 'proposals', name: 'Proposals', icon: FileText },
    { id: 'chat', name: 'Chat', icon: MessageSquare },
    { id: 'audit', name: 'Audit Log', icon: History },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-8 w-8 text-red-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Revenue Leakage Detection Agent
                </h1>
                <p className="text-sm text-gray-500">
                  AI-powered financial investigation and correction
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                    ${isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'investigation' && (
          <div className="space-y-6">
            <InvestigationPanel onInvestigationComplete={setInvestigationResults} />
            
            {investigationResults && (
              <>
                {/* Summary Stats */}
                {investigationResults.summary && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="text-sm font-medium text-gray-500">Total Findings</div>
                      <div className="mt-2 text-3xl font-bold text-gray-900">
                        {investigationResults.summary.total_findings}
                      </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="text-sm font-medium text-gray-500">Critical Issues</div>
                      <div className="mt-2 text-3xl font-bold text-red-600">
                        {investigationResults.summary.by_severity?.critical || 0}
                      </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="text-sm font-medium text-gray-500">Warnings</div>
                      <div className="mt-2 text-3xl font-bold text-yellow-600">
                        {investigationResults.summary.by_severity?.warning || 0}
                      </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                      <div className="text-sm font-medium text-gray-500">Total Impact (USD)</div>
                      <div className="mt-2 text-3xl font-bold text-gray-900">
                        ${investigationResults.summary.total_impact_usd?.toLocaleString() || 0}
                      </div>
                    </div>
                  </div>
                )}

                <FindingsTable findings={investigationResults.findings || []} />
                <ProposalsTable proposals={investigationResults.proposals || []} />
              </>
            )}
          </div>
        )}

        {activeTab === 'proposals' && (
          <ProposalsTable proposals={proposalsData?.proposals || []} />
        )}

        {activeTab === 'chat' && (
          <ChatInterface />
        )}

        {activeTab === 'audit' && (
          <AuditLogViewer />
        )}
      </main>
    </div>
  )
}

export default Dashboard

