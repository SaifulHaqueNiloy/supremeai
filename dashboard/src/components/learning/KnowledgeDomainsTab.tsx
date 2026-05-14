import React from 'react';
import { Card, Button, List, Typography, Space, Tag, Empty } from 'antd';
import { ReloadOutlined, BookOutlined, PlayCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface KnowledgeDomain {
  id: string;
  name: string;
  status: string;
  keywords: string[];
  knowledgeCount: number;
}

interface KnowledgeDomainsTabProps {
  domains: KnowledgeDomain[];
  onRefresh: () => void;
  onViewKnowledge: (id: string) => void;
}

const KnowledgeDomainsTab: React.FC<KnowledgeDomainsTabProps> = ({
  domains,
  onRefresh,
  onViewKnowledge,
}) => {
  return (
    <Card bordered={false} className="glass-card">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0, color: '#fff' }}>Knowledge Domains</Title>
        <Button icon={<ReloadOutlined />} onClick={onRefresh}>Refresh</Button>
      </div>
      <List
        dataSource={domains}
        renderItem={domain => (
          <List.Item
            actions={[
              <Button type="link" onClick={() => onViewKnowledge(domain.id)}>View Knowledge</Button>,
              <Button type="link" icon={<PlayCircleOutlined />}>Process Job</Button>
            ]}
          >
            <List.Item.Meta
              avatar={<BookOutlined style={{ fontSize: 24, color: '#3b82f6' }} />}
              title={<span style={{ color: '#fff', fontWeight: 600 }}>{domain.name}</span>}
              description={
                <Space wrap>
                  {domain.keywords.map(k => <Tag key={k}>{k}</Tag>)}
                </Space>
              }
            />
            <div style={{ textAlign: 'right', marginRight: 24 }}>
              <Tag color={domain.status === 'LEARNING' ? 'processing' : 'success'}>
                {domain.status}
              </Tag>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>Nodes: {domain.knowledgeCount}</Text>
            </div>
          </List.Item>
        )}
        locale={{ emptyText: <Empty description="কোনো ডোমেইন পাওয়া যায়নি" /> }}
      />
    </Card>
  );
};

export default KnowledgeDomainsTab;
