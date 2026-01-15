import { PlusOutlined } from '@ant-design/icons';
import {
  ActionType,
  ModalForm,
  PageContainer,
  ProFormCheckbox,
  ProFormSelect,
  ProFormText,
  ProTable,
} from '@ant-design/pro-components';
import { Button, Form, message } from 'antd';
import React, { useMemo, useRef, useState } from 'react';

import type { Account, AccountType, CreateAccountReq, PatchAccountReq } from '@/services/accounts';
import { createAccount, listAccounts, patchAccount } from '@/services/accounts';
import type { Institution } from '@/services/institutions';
import { createInstitution, listInstitutions } from '@/services/institutions';

import styles from './index.less';

type AccountFormValues = {
  name: string;
  institution_id?: number | null;
  type: AccountType;
  currency?: string;
  is_liquid?: boolean;
};

type InstitutionFormValues = {
  name: string;
};

const Accounts: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [institutionCreateOpen, setInstitutionCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Account | undefined>(undefined);
  const [accountForm] = Form.useForm<AccountFormValues>();
  const [institutionForm] = Form.useForm<InstitutionFormValues>();

  const institutionNameById = useMemo(() => {
    const map = new Map<number, string>();
    institutions.forEach((i) => map.set(i.id, i.name));
    return map;
  }, [institutions]);

  const loadInstitutions = async () => {
    try {
      const resp = await listInstitutions();
      setInstitutions(resp.items);
    } catch (e) {
      message.error('加载机构列表失败');
      setInstitutions([]);
    }
  };

  const accountTypeEnum: Record<AccountType, { text: string }> = {
    cash: { text: '现金' },
    debit: { text: '银行卡' },
    credit: { text: '信用卡' },
    investment_cash: { text: '投资账户' },
    other: { text: '其他' },
  };

  return (
    <PageContainer
      header={{
        title: '账户',
      }}
      extra={[
        <Button
          key="create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={async () => {
            await loadInstitutions();
            accountForm.resetFields();
            setCreateOpen(true);
          }}
        >
          新建账户
        </Button>,
      ]}
    >
      <div className={styles.toolbar} />
      <ProTable<Account>
        actionRef={actionRef}
        rowKey="id"
        search={false}
        request={async () => {
          await loadInstitutions();
          const resp = await listAccounts();
          return {
            data: resp.items,
            success: true,
          };
        }}
        columns={[
          {
            title: '账户名',
            dataIndex: 'name',
          },
          {
            title: '类型',
            dataIndex: 'type',
            valueEnum: accountTypeEnum,
          },
          {
            title: '机构',
            dataIndex: 'institution_id',
            render: (_, record) => {
              if (!record.institution_id) return '-';
              return institutionNameById.get(record.institution_id) || String(record.institution_id);
            },
          },
          {
            title: '计入可用现金',
            dataIndex: 'is_liquid',
            render: (_, record) => (record.is_liquid ? '✓' : '×'),
          },
          {
            title: '操作',
            valueType: 'option',
            render: (_, record) => [
              <a
                key="edit"
                onClick={async () => {
                  await loadInstitutions();
                  setEditing(record);
                  accountForm.setFieldsValue({
                    name: record.name,
                    institution_id: record.institution_id,
                    type: record.type,
                    currency: record.currency,
                    is_liquid: record.is_liquid,
                  });
                  setEditOpen(true);
                }}
              >
                编辑
              </a>,
            ],
          },
        ]}
      />

      <ModalForm<AccountFormValues>
        form={accountForm}
        title="新建账户"
        open={createOpen}
        onOpenChange={(v) => setCreateOpen(v)}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          try {
            const payload: CreateAccountReq = {
              name: values.name,
              institution_id: values.institution_id ?? null,
              type: values.type,
              currency: values.currency || 'CNY',
              is_liquid: values.is_liquid,
            };
            await createAccount(payload);
            message.success('创建成功');
            actionRef.current?.reload();
            return true;
          } catch (e) {
            message.error('创建失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="名称" rules={[{ required: true }]} />
        <ProFormSelect
          name="institution_id"
          label="机构"
          options={institutions.map((i) => ({ label: i.name, value: i.id }))}
          fieldProps={{
            allowClear: true,
            dropdownRender: (menu) => (
              <div>
                {menu}
                <div>
                  <Button
                    type="link"
                    onClick={() => {
                      institutionForm.resetFields();
                      setInstitutionCreateOpen(true);
                    }}
                  >
                    新建机构
                  </Button>
                </div>
              </div>
            ),
          }}
        />
        <ProFormSelect
          name="type"
          label="类型"
          valueEnum={accountTypeEnum}
          rules={[{ required: true }]}
          fieldProps={{
            onChange: (v) => {
              if (v === 'credit') {
                const current = accountForm.getFieldValue('is_liquid');
                if (current === undefined) {
                  accountForm.setFieldsValue({ is_liquid: false });
                }
              }
            },
          }}
        />
        <ProFormText name="currency" label="币种" initialValue="CNY" />
        <ProFormCheckbox name="is_liquid">计入可用现金</ProFormCheckbox>
      </ModalForm>

      <ModalForm<AccountFormValues>
        form={accountForm}
        title="编辑账户"
        open={editOpen}
        onOpenChange={(v) => {
          setEditOpen(v);
          if (!v) {
            setEditing(undefined);
          }
        }}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          if (!editing) return false;
          try {
            const payload: PatchAccountReq = {
              name: values.name,
              institution_id: values.institution_id ?? null,
              type: values.type,
              currency: values.currency,
              is_liquid: values.is_liquid,
            };
            await patchAccount(editing.id, payload);
            message.success('保存成功');
            actionRef.current?.reload();
            return true;
          } catch (e) {
            message.error('保存失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="名称" rules={[{ required: true }]} />
        <ProFormSelect
          name="institution_id"
          label="机构"
          options={institutions.map((i) => ({ label: i.name, value: i.id }))}
          fieldProps={{ allowClear: true }}
        />
        <ProFormSelect
          name="type"
          label="类型"
          valueEnum={accountTypeEnum}
          rules={[{ required: true }]}
        />
        <ProFormText name="currency" label="币种" />
        <ProFormCheckbox name="is_liquid">计入可用现金</ProFormCheckbox>
      </ModalForm>

      <ModalForm<InstitutionFormValues>
        form={institutionForm}
        title="新建机构"
        open={institutionCreateOpen}
        onOpenChange={(v) => setInstitutionCreateOpen(v)}
        modalProps={{ destroyOnClose: true }}
        onFinish={async (values) => {
          try {
            const created = await createInstitution({ name: values.name });
            message.success('创建成功');
            await loadInstitutions();
            accountForm.setFieldsValue({ institution_id: created.id });
            return true;
          } catch (e) {
            message.error('创建失败');
            return false;
          }
        }}
      >
        <ProFormText name="name" label="机构名称" rules={[{ required: true }]} />
      </ModalForm>
    </PageContainer>
  );
};

export default Accounts;
