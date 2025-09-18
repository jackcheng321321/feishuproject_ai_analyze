<template>
  <div class="task-create">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="page-title">{{ isEdit ? '编辑任务' : '创建任务' }}</h1>
      </div>
      <div class="header-actions">
        <el-button @click="resetForm">重置</el-button>
        <el-button 
          type="primary" 
          @click="submitForm" 
          :loading="submitLoading"
        >
          {{ isEdit ? '更新任务' : '创建任务' }}
        </el-button>
      </div>
    </div>

    <!-- 表单内容 -->
    <div class="page-container">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="task-form"
      >
        <!-- 基本信息 -->
        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><InfoFilled /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="任务名称" prop="name">
                <el-input
                  v-model="form.name"
                  placeholder="请输入任务名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
            </el-col>

          </el-row>
          
          <el-form-item label="任务描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="请输入任务描述"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          
          <el-row :gutter="20">

            <el-col :xs="24" :sm="12">
              <el-form-item label="状态">
                <el-switch
                  v-model="form.is_active"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 配置信息 -->
        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Setting /></el-icon>
              <span>配置信息</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="AI模型" prop="ai_model_id">
                <el-select
                  v-model="form.ai_model_id"
                  placeholder="请选择AI模型"
                  style="width: 100%"
                  filterable
                  @focus="loadModelConfigs"
                >
                  <el-option
                    v-for="model in modelConfigs"
                    :key="model.id"
                    :label="`${model.name} (${model.model_type})`"
                    :value="model.id"
                    :disabled="!model.is_active"
                  >
                    <div class="model-option">
                      <span class="model-name">{{ model.name }}</span>
                      <el-tag size="small" :type="model.is_active ? 'success' : 'danger'">
                        {{ model.is_active ? '可用' : '不可用' }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="Webhook" prop="webhook_id">
            <el-select
              v-model="form.webhook_id"
              placeholder="请选择Webhook"
              style="width: 100%"
              filterable
              @focus="loadWebhookConfigs"
              @change="handleWebhookChange"
            >
              <el-option
                v-for="webhook in webhookConfigs"
                :key="webhook.id"
                :label="webhook.name"
                :value="webhook.id"
                :disabled="!webhook.can_be_associated"
              >
                <div class="webhook-option">
                  <span class="webhook-name">{{ webhook.name }}</span>
                  <el-tag
                    size="small"
                    :type="webhook.can_be_associated ? 'success' : 'danger'"
                  >
                    {{ webhook.restriction_reason || '可用' }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="form.enable_storage_credential">使用存储凭证获取文件</el-checkbox>
            <div class="form-tip">勾选此项表示需要从内部网盘获取文件内容</div>
          </el-form-item>
          
          <el-form-item 
            v-if="form.enable_storage_credential" 
            label="存储凭证" 
            prop="storage_credential_id"
          >
            <el-select
              v-model="form.storage_credential_id"
              placeholder="请选择存储凭证"
              style="width: 100%"
              filterable
              @focus="loadStorageConfigs"
            >
              <el-option
                v-for="storage in storageConfigs"
                :key="storage.id"
                :label="`${storage.name} (${storage.protocol_type})`"
                :value="storage.id"
                :disabled="!storage.is_active"
              >
                <div class="storage-option">
                  <span class="storage-name">{{ storage.name }}</span>
                  <el-tag size="small" :type="storage.is_active ? 'success' : 'danger'">
                    {{ storage.is_active ? '可用' : '不可用' }}
                  </el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="form.enable_rich_text_parsing">启用富文本字段解析</el-checkbox>
            <div class="form-tip">勾选此项表示Webhook返回的字段是富文本字段，需要进行二次查询获取详细内容（包括图片等）</div>
          </el-form-item>

          <el-form-item>
            <el-checkbox v-model="form.enable_multi_field_analysis">启用多字段综合分析</el-checkbox>
            <div class="form-tip">启用此项将允许从飞书项目中查询多个字段进行综合分析，而不仅仅是Webhook触发的单个字段</div>
          </el-form-item>

          <!-- 多字段配置区域 -->
          <el-form-item v-if="form.enable_multi_field_analysis" label="字段配置">
            <div class="multi-field-config">
              <div class="config-header">
                <span>配置要查询的字段及其在提示词中的占位符</span>
                <el-button
                  type="primary"
                  size="small"
                  :icon="Plus"
                  @click="addFieldConfig"
                >
                  添加字段
                </el-button>
              </div>

              <div v-if="form.multi_field_config.fields && form.multi_field_config.fields.length > 0" class="field-list">
                <div
                  v-for="(field, index) in form.multi_field_config.fields"
                  :key="index"
                  class="field-item"
                >
                  <el-row :gutter="15" class="field-config-row">
                    <el-col :span="7">
                      <el-form-item label="字段标识" :prop="`multi_field_config.fields.${index}.field_key`">
                        <el-input
                          v-model="field.field_key"
                          placeholder="如：field_a9b5af"
                          maxlength="50"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="6">
                      <el-form-item label="字段名称" :prop="`multi_field_config.fields.${index}.field_name`">
                        <el-input
                          v-model="field.field_name"
                          placeholder="如：需求描述"
                          maxlength="50"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="7">
                      <el-form-item label="字段占位符" :prop="`multi_field_config.fields.${index}.placeholder`">
                        <el-input
                          v-model="field.placeholder"
                          placeholder="如：description"
                          maxlength="30"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="4" class="delete-button-col">
                      <el-button
                        type="danger"
                        size="small"
                        :icon="Delete"
                        @click="removeFieldConfig(index)"
                        :disabled="form.multi_field_config.fields.length <= 1"
                        class="delete-field-btn"
                      >
                        删除
                      </el-button>
                    </el-col>
                  </el-row>
                </div>
              </div>

              <div v-else class="empty-field-config">
                <el-empty description="尚未配置任何字段" :image-size="60">
                  <el-button type="primary" @click="addFieldConfig">添加第一个字段</el-button>
                </el-empty>
              </div>

              <!-- 多字段查询测试按钮 -->
              <div v-if="form.multi_field_config.fields && form.multi_field_config.fields.length > 0" class="multi-field-test-section">
                <el-button
                  type="warning"
                  :icon="Connection"
                  @click="testMultiFieldQuery"
                  :loading="testingMultiField"
                  :disabled="!canTestMultiField"
                >
                  多字段查询测试
                </el-button>
                <div class="form-tip">
                  基于当前配置的字段从飞书项目中查询实际数据，验证字段配置是否正确
                </div>
              </div>

              <!-- 多字段查询测试结果显示 -->
              <el-form-item v-if="multiFieldTestResult">
                <el-card class="multi-field-test-result-card" shadow="never">
                  <template #header>
                    <div class="result-header">
                      <el-icon><Connection /></el-icon>
                      <span>多字段查询测试结果</span>
                      <el-tag
                        :type="multiFieldTestResult.success ? 'success' : 'danger'"
                        size="small"
                      >
                        {{ multiFieldTestResult.success ? '成功' : '失败' }}
                      </el-tag>
                    </div>
                  </template>

                  <div v-if="multiFieldTestResult.success" class="multi-field-result-content">
                    <div class="result-meta">
                      <span class="meta-item">成功字段: {{ multiFieldTestResult.field_count || 0 }}</span>
                      <span class="meta-item">总字段数: {{ form.multi_field_config.fields?.length || 0 }}</span>
                      <span class="meta-item">耗时: {{ multiFieldTestResult.execution_time_ms || 0 }}ms</span>
                    </div>

                    <div v-if="multiFieldTestResult.query_details" class="field-details">
                      <h5>字段查询详情：</h5>
                      <div
                        v-for="detail in multiFieldTestResult.query_details"
                        :key="detail.field_key"
                        class="field-detail-item"
                      >
                        <div class="field-detail-header">
                          <span class="field-name">{{ detail.field_name }} ({{ detail.field_key }})</span>
                          <el-tag
                            :type="detail.success ? 'success' : 'danger'"
                            size="small"
                          >
                            {{ detail.success ? '成功' : '失败' }}
                          </el-tag>
                        </div>
                        <div v-if="detail.success" class="field-value">
                          <strong>值:</strong> {{ detail.value || '空值' }}
                          <span v-if="detail.value_type" class="value-type">({{ detail.value_type }})</span>
                        </div>
                        <div v-else class="field-error">
                          <strong>错误:</strong> {{ detail.error }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else class="multi-field-error-content">
                    <el-alert
                      :title="multiFieldTestResult.error || '多字段查询测试失败'"
                      type="error"
                      show-icon
                      :closable="false"
                    />
                  </div>
                </el-card>
              </el-form-item>

              <div class="field-config-tips">
                <h5>配置说明：</h5>
                <ul>
                  <li><strong>字段标识：</strong>飞书项目中的字段ID，如 field_a9b5af</li>
                  <li><strong>字段名称：</strong>用于显示的友好名称，如"需求描述"</li>
                  <li><strong>占位符：</strong>在分析提示词中使用，如 {description} 将被替换为实际字段值</li>
                </ul>
              </div>
            </div>
          </el-form-item>
        </el-card>

        <!-- 分析配置 -->
        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><DocumentCopy /></el-icon>
              <span>分析配置</span>
            </div>
          </template>
          
          <!-- Webhook数据展示区域 -->
          <el-form-item label="数据预览" v-if="webhookPreviewData">
            <el-card class="webhook-preview-card" shadow="never">
              <el-row :gutter="20">
                <el-col :span="14">
                  <div class="webhook-data-item">
                    <label>提取字段值:</label>
                    <pre class="webhook-field-value">{{ webhookPreviewData.field_value || '未获取到数据' }}</pre>
                  </div>
                </el-col>
                <el-col :span="10">
                  <div class="webhook-data-item">
                    <label>记录ID:</label>
                    <pre class="webhook-field-value">{{ webhookPreviewData.record_id || '未获取到数据' }}</pre>
                  </div>
                </el-col>
              </el-row>
            </el-card>
            
            <!-- 存储验证按钮和结果 -->
            <div v-if="form.enable_storage_credential && form.storage_credential_id" class="storage-validation-section">
              <el-button 
                v-if="webhookPreviewData.field_value && webhookPreviewData.field_value !== '未获取到数据' && webhookPreviewData.field_value !== '暂无数据'"
                type="primary" 
                size="small" 
                :loading="validatingStorage"
                @click="validateStorageData"
              >
                验证存储访问
              </el-button>
              
              <div v-if="storageValidationResult" class="storage-validation-result">
                <el-tag 
                  :type="storageValidationResult.success ? 'success' : 'danger'"
                  size="small"
                >
                  {{ storageValidationResult.message }}
                </el-tag>
                
                <!-- 显示文件详细信息 -->
                <div v-if="storageValidationResult.success && storageValidationResult.fileInfo" class="file-details">
                  <!-- 显示文件列表（目录） -->
                  <div v-if="storageValidationResult.fileInfo.files && storageValidationResult.fileInfo.files.length > 0" class="file-list">
                    <el-text size="small" type="info">
                      包含文件：{{ storageValidationResult.fileInfo.files.slice(0, 3).join(', ') }}
                      <span v-if="storageValidationResult.fileInfo.file_count && storageValidationResult.fileInfo.file_count > 3">等{{ storageValidationResult.fileInfo.file_count }}个文件</span>
                    </el-text>
                  </div>
                  <!-- 显示单个文件信息 -->
                  <div v-else-if="storageValidationResult.fileInfo.file_name" class="file-info">
                    <el-text size="small" type="info">
                      文件：{{ storageValidationResult.fileInfo.file_name }}
                      <span v-if="storageValidationResult.fileInfo.file_size"> ({{ formatFileSize(storageValidationResult.fileInfo.file_size) }})</span>
                    </el-text>
                  </div>
                  <!-- 显示其他验证信息 -->
                  <div v-else-if="storageValidationResult.fileInfo.server || storageValidationResult.fileInfo.protocol" class="validation-info">
                    <el-text size="small" type="info">
                      <span v-if="storageValidationResult.fileInfo.protocol">{{ storageValidationResult.fileInfo.protocol.toUpperCase() }}协议</span>
                      <span v-if="storageValidationResult.fileInfo.server"> - 服务器: {{ storageValidationResult.fileInfo.server }}</span>
                      <span v-if="storageValidationResult.fileInfo.share"> - 共享: {{ storageValidationResult.fileInfo.share }}</span>
                      <span v-if="storageValidationResult.fileInfo.validation_type"> ({{ storageValidationResult.fileInfo.validation_type === 'connection_test' ? '连接测试' : '实际访问' }})</span>
                    </el-text>
                    <div v-if="storageValidationResult.fileInfo.note" class="validation-note">
                      <el-text size="small" type="warning">{{ storageValidationResult.fileInfo.note }}</el-text>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 富文本字段查询按钮和结果 -->
            <div v-if="form.enable_rich_text_parsing" class="rich-text-query-section">
              <el-button 
                v-if="webhookPreviewData.field_value && webhookPreviewData.field_value !== '未获取到数据' && webhookPreviewData.field_value !== '暂无数据'"
                type="warning" 
                size="small" 
                :loading="queryingRichText"
                @click="queryRichTextDetails"
              >
                查询富文本详情
              </el-button>
              
              <div v-if="richTextQueryResult" class="rich-text-query-result">
                <el-tag 
                  :type="richTextQueryResult.success ? 'success' : 'danger'"
                  size="small"
                >
                  {{ richTextQueryResult.success ? '富文本详情获取成功' : richTextQueryResult.message || '查询失败' }}
                </el-tag>
                
                <!-- 显示富文本详细信息 -->
                <div v-if="richTextQueryResult.success" class="rich-text-details">
                  <el-collapse v-model="activeCollapseNames" class="rich-text-collapse">
                    <el-collapse-item title="富文本文档结构" name="doc">
                      <div class="rich-text-content">
                        <pre class="rich-text-json">{{ formatJson(richTextQueryResult.doc) }}</pre>
                      </div>
                    </el-collapse-item>
                    
                    <el-collapse-item title="纯文本内容" name="text">
                      <div class="rich-text-content">
                        <pre class="rich-text-text">{{ richTextQueryResult.doc_text || '无文本内容' }}</pre>
                      </div>
                    </el-collapse-item>
                    
                    <el-collapse-item title="HTML内容" name="html">
                      <div class="rich-text-content">
                        <div class="rich-text-html" v-html="richTextQueryResult.doc_html || '无HTML内容'"></div>
                      </div>
                    </el-collapse-item>
                    
                    <el-collapse-item title="元信息" name="meta">
                      <div class="rich-text-content">
                        <p><strong>字段标识:</strong> {{ richTextQueryResult.field_key }}</p>
                        <p><strong>工作项ID:</strong> {{ richTextQueryResult.work_item_id }}</p>
                        <p><strong>工作项名称:</strong> {{ richTextQueryResult.work_item_name }}</p>
                        <p><strong>是否为空:</strong> {{ richTextQueryResult.is_empty ? '是' : '否' }}</p>
                        <p v-if="richTextQueryResult.timestamp"><strong>查询时间:</strong> {{ formatTimestamp(richTextQueryResult.timestamp) }}</p>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>
            
            <div class="form-tip">
              此数据将从选中Webhook的最近日志中获取，用于预览将要分析的数据结构
              <span v-if="form.enable_storage_credential">；启用存储凭证时可点击验证按钮测试文件访问</span>
            </div>
          </el-form-item>
          
          <el-form-item label="分析提示词" prop="analysis_prompt">
            <el-input
              ref="promptTextarea"
              v-model="form.analysis_prompt"
              type="textarea"
              :rows="6"
              :placeholder="getPromptPlaceholder()"
              maxlength="5000"
              show-word-limit
            />
            <div class="form-tip">
              <!-- 富文本占位符显示 -->
              <div v-if="form.enable_rich_text_parsing">
                <strong>富文本字段：</strong>使用以下占位符插入富文本内容：
                <br>
                <code
                  class="placeholder-code clickable"
                  @click="insertPlaceholder('field_value')"
                  title="点击插入 {field_value} 到分析提示词中 - 包含富文本中的纯文本内容（自动过滤图片）"
                >{field_value}</code>
                <span class="placeholder-desc">- 富文本的纯文本内容（图片会单独处理）</span>
                <br>
                <code
                  class="placeholder-code clickable"
                  @click="insertPlaceholder('trigger_field')"
                  title="点击插入 {trigger_field} 到分析提示词中 - 与field_value相同，语义化别名"
                >{trigger_field}</code>
                <span class="placeholder-desc">- 同{field_value}，提供语义化别名</span>
                <br>
                <div class="rich-text-note">
                  <el-icon><InfoFilled /></el-icon>
                  <span>富文本字段包含：<strong>文字内容</strong>（通过占位符插入）+ <strong>图片内容</strong>（自动发送给AI模型，无需占位符）</span>
                </div>
              </div>

              <!-- 多字段占位符显示 -->
              <div v-if="form.enable_multi_field_analysis && form.multi_field_config.fields && form.multi_field_config.fields.length > 0">
                <strong>自定义字段：</strong>使用以下占位符插入对应字段数据：
                <code
                  v-for="field in form.multi_field_config.fields"
                  :key="field.field_key"
                  class="placeholder-code clickable"
                  @click="insertPlaceholder(field.placeholder)"
                  :title="`点击插入 {${field.placeholder}} 到分析提示词中`"
                >
                  {{ '{' + field.placeholder + '}' }}
                </code>
              </div>

              <!-- 综合使用说明 -->
              <div v-if="form.enable_rich_text_parsing || (form.enable_multi_field_analysis && form.multi_field_config.fields && form.multi_field_config.fields.length > 0)">
                <div style="margin-top: 8px; color: #666; font-size: 12px;">
                  <el-icon><InfoFilled /></el-icon>
                  点击占位符可快速插入到提示词中，如果不使用占位符，富文本字段数据将自动追加到提示词后面
                </div>
              </div>

              <!-- 默认提示（无特殊功能启用时） -->
              <div v-if="!form.enable_rich_text_parsing && !(form.enable_multi_field_analysis && form.multi_field_config.fields && form.multi_field_config.fields.length > 0)">
                <strong>基础模式：</strong>请输入分析提示词，字段数据将自动追加到提示词后面
              </div>
            </div>
          </el-form-item>
          
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="最大Token数">
                <el-input-number
                  v-model="form.max_tokens"
                  :min="100"
                  :max="32000"
                  :step="100"
                  style="width: 100%"
                  controls-position="right"
                />
                <div class="form-tip">AI响应的最大Token数量</div>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="温度参数">
                <el-slider
                  v-model="form.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                  :input-size="'small'"
                />
                <div class="form-tip">控制AI响应的随机性，0-2之间</div>
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- AI分析测试区域 -->
          <el-form-item>
            <el-button
              type="success"
              :icon="Cpu"
              @click="testAiAnalysis"
              :loading="testingAi"
              :disabled="!canTestAi"
              style="margin-right: 10px;"
            >
              AI分析测试
            </el-button>
            <div class="form-tip">
              基于当前获取到的数据预览进行AI分析测试，验证提示词和参数配置
            </div>
          </el-form-item>
          
          <!-- AI测试结果显示 -->
          <el-form-item v-if="aiTestResult">
            <el-card class="ai-test-result-card" shadow="never">
              <template #header>
                <div class="result-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>AI分析结果</span>
                  <el-tag 
                    :type="aiTestResult.success ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ aiTestResult.success ? '成功' : '失败' }}
                  </el-tag>
                </div>
              </template>
              
              <div v-if="aiTestResult.success" class="ai-result-content">
                <div class="result-meta">
                  <span class="meta-item">模型: {{ aiTestResult.model_name }}</span>
                  <span class="meta-item">Token用量: {{ aiTestResult.token_usage?.total_tokens || 0 }}</span>
                  <span class="meta-item">耗时: {{ aiTestResult.response_time }}ms</span>
                </div>
                <div class="result-text">
                  <pre class="ai-response">{{ aiTestResult.content }}</pre>
                </div>
              </div>
              
              <div v-else class="ai-error-content">
                <el-alert
                  :title="aiTestResult.error || 'AI分析失败'"
                  type="error"
                  show-icon
                  :closable="false"
                />
              </div>
            </el-card>
          </el-form-item>
        </el-card>

        <!-- 数据写入配置 -->
        <el-card class="form-section" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Upload /></el-icon>
              <span>数据写入配置</span>
            </div>
          </template>
          
          <el-form-item label="飞书字段ID" prop="feishu_field_id">
            <el-input
              v-model="form.feishu_write_config.field_id"
              placeholder="请输入要更新的飞书字段ID，如：field_a9b5af"
              maxlength="100"
            />
            <div class="form-tip">
              AI分析结果将写入到飞书项目中具有此ID的字段中
            </div>
          </el-form-item>
          
          <!-- AI分析结果写入测试按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              :icon="Upload"
              @click="testFeishuWrite"
              :loading="testingFeishuWrite"
              :disabled="!canTestFeishuWrite"
            >
              AI分析结果写入测试
            </el-button>
            <div class="form-tip">
              基于当前的AI分析结果和Webhook数据，测试写入飞书项目的功能
            </div>
          </el-form-item>
          
          <!-- 飞书写入测试结果显示 -->
          <el-form-item v-if="feishuWriteTestResult">
            <el-card class="feishu-write-test-result-card" shadow="never">
              <template #header>
                <div class="result-header">
                  <el-icon><Upload /></el-icon>
                  <span>飞书写入测试结果</span>
                  <el-tag 
                    :type="feishuWriteTestResult.success ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ feishuWriteTestResult.success ? '成功' : '失败' }}
                  </el-tag>
                </div>
              </template>
              
              <div v-if="feishuWriteTestResult.success" class="write-result-content">
                <div class="result-meta">
                  <span class="meta-item">项目: {{ feishuWriteTestResult.project_key }}</span>
                  <span class="meta-item">工作项: {{ feishuWriteTestResult.work_item_id }}</span>
                  <span class="meta-item">字段: {{ feishuWriteTestResult.field_key }}</span>
                </div>
                <div class="result-message">
                  <div class="success-message">{{ feishuWriteTestResult.message }}</div>
                  <div v-if="feishuWriteTestResult.write_response" class="write-response">
                    <strong>写入响应:</strong>
                    <pre>{{ formatJson(feishuWriteTestResult.write_response) }}</pre>
                  </div>
                </div>
              </div>
              
              <div v-else class="write-error-content">
                <el-alert
                  :title="feishuWriteTestResult.error || '写入测试失败'"
                  type="error"
                  show-icon
                  :closable="false"
                />
                <div v-if="feishuWriteTestResult.details" class="error-details">
                  <pre>{{ feishuWriteTestResult.details }}</pre>
                </div>
              </div>
            </el-card>
          </el-form-item>
        </el-card>

      </el-form>
    </div>

    <!-- Cron帮助对话框 -->
    <el-dialog
      v-model="cronHelperVisible"
      title="Cron表达式帮助"
      width="600px"
    >
      <div class="cron-helper">
        <h4>Cron表达式格式：</h4>
        <p><code>分 时 日 月 周</code></p>
        
        <h4>常用示例：</h4>
        <ul>
          <li><code>0 0 * * *</code> - 每天0点执行</li>
          <li><code>0 */2 * * *</code> - 每2小时执行一次</li>
          <li><code>0 9 * * 1-5</code> - 工作日上午9点执行</li>
          <li><code>0 0 1 * *</code> - 每月1号0点执行</li>
          <li><code>0 0 * * 0</code> - 每周日0点执行</li>
        </ul>
        
        <h4>字段说明：</h4>
        <ul>
          <li>分：0-59</li>
          <li>时：0-23</li>
          <li>日：1-31</li>
          <li>月：1-12</li>
          <li>周：0-7（0和7都表示周日）</li>
        </ul>
        
        <h4>特殊字符：</h4>
        <ul>
          <li><code>*</code> - 匹配任意值</li>
          <li><code>?</code> - 不指定值</li>
          <li><code>-</code> - 范围，如1-5</li>
          <li><code>,</code> - 列举，如1,3,5</li>
          <li><code>/</code> - 步长，如*/2</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  ArrowLeft,
  InfoFilled,
  Setting,
  DocumentCopy,
  Upload,
  Delete,
  Plus,
  Connection,
  Cpu,
  ChatDotRound
} from '@element-plus/icons-vue'
import { taskApi, modelConfigApi, storageConfigApi, webhookApi } from '@/api'
import type { AnalysisTask, AnalysisTaskCreate, AIModel, StorageCredential, Webhook } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const formRef = ref<FormInstance>()
const promptTextarea = ref()
const submitLoading = ref(false)
const testingFeishu = ref(false)
const testingFeishuWrite = ref(false)
const cronHelperVisible = ref(false)
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()
const validatingStorage = ref(false)
const testingAi = ref(false)
const queryingRichText = ref(false)
const testingMultiField = ref(false)
const activeCollapseNames = ref(['text'])

// 存储验证结果
const storageValidationResult = ref<{
  success: boolean
  message: string
  fileInfo?: {
    exists: boolean
    is_directory: boolean
    file_count?: number
    files?: string[]
    file_size?: number
    file_name?: string
    content_length?: string
    content_type?: string
    server?: string
    protocol?: string
    share?: string
    validation_type?: string
    note?: string
  }
} | null>(null)

// AI测试结果
const aiTestResult = ref<{
  success: boolean
  content?: string
  error?: string
  model_name?: string
  token_usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  response_time?: number
} | null>(null)

// 富文本查询结果
const richTextQueryResult = ref<{
  success: boolean
  message?: string
  field_key?: string
  doc?: string
  doc_text?: string
  doc_html?: string
  is_empty?: boolean
  work_item_id?: string
  work_item_name?: string
  webhook_info?: any
  timestamp?: string
  error?: string
} | null>(null)

// 飞书写入测试结果
const feishuWriteTestResult = ref<{
  success: boolean
  message?: string
  project_key?: string
  work_item_id?: string
  work_item_type_key?: string
  field_key?: string
  write_response?: any
  error?: string
  details?: string
} | null>(null)

// 多字段测试结果
const multiFieldTestResult = ref<{
  success: boolean
  message?: string
  project_key?: string
  work_item_id?: string
  work_item_type_key?: string
  field_data?: any
  field_count?: number
  failed_fields?: string[]
  query_details?: Array<{
    field_key: string
    field_name: string
    success: boolean
    value?: any
    value_type?: string
    has_value?: boolean
    error?: string
  }>
  timestamp?: string
  execution_time_ms?: number
  error?: string
} | null>(null)

// 配置选项
const modelConfigs = ref<AIModel[]>([])
const storageConfigs = ref<StorageCredential[]>([])
const webhookConfigs = ref<Webhook[]>([])

// 计算属性
const isEdit = computed(() => !!route.params.id)
const taskId = computed(() => route.params.id as string)

// 判断是否可以进行AI测试
const canTestAi = computed(() => {
  return !!(
    form.ai_model_id && 
    form.analysis_prompt && 
    webhookPreviewData.value && 
    (webhookPreviewData.value.field_value && 
     webhookPreviewData.value.field_value !== '未获取到数据' &&
     webhookPreviewData.value.field_value !== '暂无数据' &&
     webhookPreviewData.value.field_value !== '加载失败')
  )
})

// 判断是否可以进行飞书写入测试
const canTestFeishuWrite = computed(() => {
  return !!(
    aiTestResult.value?.success &&
    aiTestResult.value?.content &&
    form.feishu_write_config.field_id &&
    webhookPreviewData.value?.record_id &&
    webhookPreviewData.value.record_id !== '未获取到数据' &&
    webhookPreviewData.value.record_id !== '暂无数据' &&
    webhookPreviewData.value.record_id !== '加载失败'
  )
})

// 判断是否可以进行多字段测试
const canTestMultiField = computed(() => {
  return !!(
    form.enable_multi_field_analysis &&
    form.multi_field_config?.fields &&
    form.multi_field_config.fields.length > 0 &&
    webhookPreviewData.value?.record_id &&
    webhookPreviewData.value.record_id !== '未获取到数据' &&
    webhookPreviewData.value.record_id !== '暂无数据' &&
    webhookPreviewData.value.record_id !== '加载失败'
  )
})

// Webhook数据预览
const webhookPreviewData = ref<{
  field_value: string | null
  record_id: string | null
  project_key?: string | null
  work_item_type_key?: string | null
} | null>(null)


// 表单数据
const form = reactive<AnalysisTaskCreate & {
  enable_storage_credential?: boolean
  enable_rich_text_parsing?: boolean
  enable_multi_field_analysis?: boolean
  multi_field_config?: {
    fields: Array<{
      field_key: string
      field_name: string
      placeholder: string
      required: boolean
    }>
  }
}>({
  name: '',
  description: '',
  is_active: true,
  ai_model_id: null,
  storage_credential_id: undefined,
  webhook_id: null,
  analysis_prompt: '',
  temperature: 1.0,
  max_tokens: 10000,
  is_scheduled: false,
  data_extraction_config: {},
  prompt_template: '',
  feishu_config: {},
  field_mapping: {},
  enable_storage_credential: false,
  enable_rich_text_parsing: false,
  enable_multi_field_analysis: false,
  multi_field_config: {
    fields: []
  },
  feishu_write_config: {
    field_id: ''
  }
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在2 到 100 个字符', trigger: 'blur' }
  ],
  ai_model_id: [
    {
      required: true,
      message: '请选择AI模型',
      trigger: 'change',
      validator: (rule: any, value: any, callback: Function) => {
        if (!value || value === 0 || value === null) {
          callback(new Error('请选择AI模型'))
        } else {
          callback()
        }
      }
    }
  ],
  webhook_id: [
    {
      required: true,
      message: '请选择Webhook',
      trigger: 'change',
      validator: (rule: any, value: any, callback: Function) => {
        if (!value || value === 0 || value === null) {
          callback(new Error('请选择Webhook'))
        } else {
          callback()
        }
      }
    }
  ],
  storage_credential_id: [
    {
      validator: (rule: any, value: any, callback: Function) => {
        if (form.enable_storage_credential && !value) {
          callback(new Error('启用存储凭证时必须选择一个凭证'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  analysis_prompt: [
    { required: true, message: '请输入分析提示词', trigger: 'blur' },
    { max: 5000, message: '长度不能超过 5000 个字符', trigger: 'blur' }
  ],
  feishu_field_id: [
    { 
      validator: (rule: any, value: any, callback: Function) => {
        const fieldId = form.feishu_write_config.field_id
        if (!fieldId || fieldId.trim() === '') {
          callback(new Error('请输入飞书字段ID'))
        } else if (fieldId.length > 100) {
          callback(new Error('飞书字段ID长度不能超过100个字符'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取提示词占位符说明
const getPromptPlaceholder = () => {
  const availablePlaceholders = []

  // 如果启用富文本解析，添加富文本占位符
  if (form.enable_rich_text_parsing) {
    availablePlaceholders.push('{field_value}', '{trigger_field}')
  }

  // 如果启用多字段分析，添加自定义字段占位符
  if (form.enable_multi_field_analysis && form.multi_field_config?.fields && form.multi_field_config.fields.length > 0) {
    const customPlaceholders = form.multi_field_config.fields.map(field => `{${field.placeholder}}`)
    availablePlaceholders.push(...customPlaceholders)
  }

  if (availablePlaceholders.length > 0) {
    const placeholderText = availablePlaceholders.join(', ')

    // 根据启用的功能提供不同的示例
    let example = ''
    if (form.enable_rich_text_parsing && form.enable_multi_field_analysis) {
      example = '例如：请分析富文本内容：{field_value}，并结合描述信息：{description} 评估优先级：{priority}'
    } else if (form.enable_rich_text_parsing) {
      example = '例如：请分析以下富文本内容：{field_value}，并给出改进建议'
    } else if (form.enable_multi_field_analysis) {
      example = '例如：请分析以下需求内容：{description}，并评估其优先级：{priority}'
    }

    return `请输入分析提示词，可使用占位符：${placeholderText}。${example}`
  }

  return '请输入分析提示词，描述你希望AI如何分析文件内容'
}

// 添加字段配置
const addFieldConfig = () => {
  if (!form.multi_field_config) {
    form.multi_field_config = { fields: [] }
  }
  form.multi_field_config.fields.push({
    field_key: '',
    field_name: '',
    placeholder: '',
    required: true // 保持后端兼容性，但前端不显示
  })
}

// 移除字段配置
const removeFieldConfig = (index: number) => {
  if (form.multi_field_config?.fields && form.multi_field_config.fields.length > 1) {
    form.multi_field_config.fields.splice(index, 1)
  }
}

// 插入占位符到分析提示词中
const insertPlaceholder = (placeholder: string) => {
  const placeholderText = `{${placeholder}}`

  // 获取textarea的DOM元素
  const textareaEl = promptTextarea.value?.$refs?.textarea || promptTextarea.value?.textarea

  if (textareaEl) {
    const startPos = textareaEl.selectionStart
    const endPos = textareaEl.selectionEnd
    const currentValue = form.analysis_prompt || ''

    // 在光标位置插入占位符
    const newValue = currentValue.substring(0, startPos) + placeholderText + currentValue.substring(endPos)

    // 更新表单值
    form.analysis_prompt = newValue

    // 聚焦到textarea并设置光标位置
    nextTick(() => {
      textareaEl.focus()
      const newCursorPos = startPos + placeholderText.length
      textareaEl.setSelectionRange(newCursorPos, newCursorPos)
    })

    ElMessage.success(`已插入占位符 ${placeholderText}`)
  } else {
    // 如果无法获取到DOM元素，则在末尾追加
    const currentValue = form.analysis_prompt || ''
    form.analysis_prompt = currentValue + (currentValue ? ' ' : '') + placeholderText
    ElMessage.success(`已添加占位符 ${placeholderText}`)
  }
}

// 测试多字段查询
const testMultiFieldQuery = async () => {
  if (!canTestMultiField.value) {
    ElMessage.error('请先配置字段并确保有有效的webhook数据')
    return
  }

  testingMultiField.value = true
  multiFieldTestResult.value = null

  try {
    // 构建测试请求
    const testRequest = {
      multi_field_config: {
        fields: form.multi_field_config!.fields
      },
      webhook_data: {
        project_key: webhookPreviewData.value?.project_key || "default_project",
        work_item_type_key: webhookPreviewData.value?.work_item_type_key || "story",
        id: webhookPreviewData.value?.record_id || ""
      },
      plugin_id: "", // 将由后端从环境变量获取
      plugin_secret: "", // 将由后端从环境变量获取
      user_key: "" // 将由后端从环境变量获取
    }

    console.log('发送多字段查询测试请求:', testRequest)

    // 调用API
    const result = await taskApi.testMultiFieldQuery(testRequest)

    multiFieldTestResult.value = {
      success: result.success,
      message: result.message,
      project_key: result.project_key,
      work_item_id: result.work_item_id,
      work_item_type_key: result.work_item_type_key,
      field_data: result.field_data,
      field_count: result.field_count,
      failed_fields: result.failed_fields,
      query_details: result.query_details,
      timestamp: result.timestamp,
      execution_time_ms: result.execution_time_ms,
      error: result.error
    }

    if (result.success) {
      ElMessage.success(`多字段查询测试成功，成功查询 ${result.field_count || 0} 个字段`)
    } else {
      ElMessage.error(`多字段查询测试失败: ${result.error || result.message}`)
    }

  } catch (error: any) {
    console.error('多字段查询测试失败:', error)

    let errorMessage = '测试失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }

    multiFieldTestResult.value = {
      success: false,
      error: errorMessage,
      timestamp: new Date().toISOString()
    }

    ElMessage.error(`多字段查询测试失败: ${errorMessage}`)
  } finally {
    testingMultiField.value = false
  }
}

// 方法
const loadModelConfigs = async () => {
  if (modelConfigs.value.length > 0) return
  
  try {
    const response = await modelConfigApi.getList({ page: 1, size: 100 })
    modelConfigs.value = response.items
  } catch (error) {
    console.error('加载AI模型配置失败:', error)
  }
}

const loadStorageConfigs = async () => {
  if (storageConfigs.value.length > 0) return
  
  try {
    const response = await storageConfigApi.getList({ page: 1, size: 100 })
    storageConfigs.value = response.items
  } catch (error) {
    console.error('加载存储配置失败:', error)
  }
}

const loadWebhookConfigs = async () => {
  if (webhookConfigs.value.length > 0) return

  try {
    const response = await webhookApi.getList({ page: 1, size: 100 })

    // 为每个webhook检查关联状态
    const webhooksWithStatus = await Promise.all(
      response.items.map(async (webhook) => {
        try {
          const statusResponse = await webhookApi.checkAssociationStatus(webhook.id)

          // 基于关联状态重新计算可用性
          let canBeAssociated = false
          let restrictionReason = null

          if (!webhook.is_active) {
            // Webhook未启用
            canBeAssociated = false
            restrictionReason = "Webhook未启用"
          } else if (statusResponse.associated_task_count === 0) {
            // 没有关联任何任务，直接可用
            canBeAssociated = true
            restrictionReason = null
          } else {
            // 有关联任务的情况下
            if (isEdit.value) {
              // 编辑模式：检查是否只关联了当前任务
              const currentTaskId = parseInt(taskId.value)
              const isAssociatedWithCurrentTask = statusResponse.associated_tasks.some(
                task => task.id === currentTaskId
              )

              if (isAssociatedWithCurrentTask) {
                // 如果关联了当前任务，计算其他任务数量
                const otherActiveTasks = statusResponse.associated_tasks.filter(
                  task => task.id !== currentTaskId && task.is_active
                )

                if (otherActiveTasks.length === 0) {
                  // 只关联了当前任务或关联的其他任务都是非活跃状态
                  canBeAssociated = true
                  restrictionReason = null
                } else {
                  // 还关联了其他活跃任务
                  canBeAssociated = false
                  restrictionReason = `已关联其他 ${otherActiveTasks.length} 个启用任务`
                }
              } else {
                // 没有关联当前任务，但关联了其他任务
                const activeTasksCount = statusResponse.associated_tasks.filter(task => task.is_active).length
                canBeAssociated = false
                restrictionReason = `已关联 ${activeTasksCount} 个启用任务`
              }
            } else {
              // 创建模式：有任何启用状态的关联任务就不可用
              const activeTasksCount = statusResponse.associated_tasks.filter(task => task.is_active).length
              if (activeTasksCount > 0) {
                canBeAssociated = false
                restrictionReason = `已关联 ${activeTasksCount} 个启用任务`
              } else {
                // 所有关联任务都是非启用状态，可以使用
                canBeAssociated = true
                restrictionReason = null
              }
            }
          }

          return {
            ...webhook,
            can_be_associated: canBeAssociated,
            restriction_reason: restrictionReason,
            associated_task_count: statusResponse.associated_task_count,
            associated_tasks: statusResponse.associated_tasks
          }
        } catch (error) {
          console.error(`检查webhook ${webhook.id} 关联状态失败:`, error)
          // 如果检查失败，回退到原有逻辑
          return {
            ...webhook,
            can_be_associated: webhook.is_active,
            restriction_reason: webhook.is_active ? null : 'Webhook未启用',
            associated_task_count: 0,
            associated_tasks: []
          }
        }
      })
    )

    webhookConfigs.value = webhooksWithStatus
  } catch (error) {
    console.error('加载Webhook配置失败:', error)
  }
}

// 加载Webhook预览数据
const loadWebhookPreviewData = async () => {
  if (!form.webhook_id) {
    webhookPreviewData.value = null
    return
  }
  
  try {
    console.log('正在加载Webhook预览数据，webhook_id:', form.webhook_id)
    const response = await webhookApi.getLatestLog(form.webhook_id)
    
    console.log('API返回的原始响应:', response)
    
    webhookPreviewData.value = {
      field_value: response.field_value || '暂无数据',
      record_id: response.record_id || '暂无数据',
      project_key: response.project_key || null,
      work_item_type_key: response.work_item_type_key || null
    }
    
    console.log('Webhook预览数据设置后:', webhookPreviewData.value)
    
    // 如果获取到了有效数据，清空验证结果
    if (response.field_value && response.field_value !== '暂无数据') {
      storageValidationResult.value = null
    }
  } catch (error) {
    console.error('加载Webhook预览数据失败:', error)
    webhookPreviewData.value = {
      field_value: '加载失败',
      record_id: '加载失败',
      project_key: null,
      work_item_type_key: null
    }
    ElMessage.warning('获取Webhook数据预览失败，请检查是否有请求日志')
  }
}

// AI分析结果写入测试方法
const testFeishuWrite = async () => {
  if (!canTestFeishuWrite.value) {
    ElMessage.error('请先完成AI分析测试并配置飞书字段ID')
    return
  }
  
  testingFeishuWrite.value = true
  feishuWriteTestResult.value = null
  
  try {
    // 构建测试请求数据
    const testRequest = {
      field_key: form.feishu_write_config.field_id,
      analysis_result: aiTestResult.value?.content,
      webhook_data: webhookPreviewData.value,
      // 从webhook数据中提取项目信息
      project_key: webhookPreviewData.value?.project_key || "default_project_key", // 从webhook数据提取
      work_item_type_key: webhookPreviewData.value?.work_item_type_key || "story", // 从webhook数据提取
      work_item_id: String(webhookPreviewData.value?.record_id || ''), // 确保转换为字符串
      // 认证配置将由后端自动处理
      plugin_token: "", // 将由后端自动获取
      user_key: "" // 将由后端从环境变量获取
    }
    
    console.log('发送飞书写入测试请求:', testRequest)
    
    // 调用后端API（需要新增这个API）
    const result = await taskApi.testFeishuWrite(testRequest)
    
    feishuWriteTestResult.value = {
      success: result.success,
      message: result.message,
      project_key: result.project_key,
      work_item_id: result.work_item_id,
      work_item_type_key: result.work_item_type_key,
      field_key: result.field_key,
      write_response: result.write_response,
      error: result.error,
      details: result.details
    }
    
    if (result.success) {
      ElMessage.success('飞书写入测试成功')
    } else {
      ElMessage.error(`飞书写入测试失败: ${result.error || result.message}`)
    }
  } catch (error: any) {
    console.error('飞书写入测试失败:', error)
    
    let errorMessage = '测试失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    feishuWriteTestResult.value = {
      success: false,
      error: errorMessage,
      details: JSON.stringify(error.response?.data || error.message || '未知错误', null, 2)
    }
    
    ElMessage.error(`飞书写入测试失败: ${errorMessage}`)
  } finally {
    testingFeishuWrite.value = false
  }
}

// 监听Webhook选择变化
const handleWebhookChange = () => {
  loadWebhookPreviewData()
  // 清空之前的验证结果
  storageValidationResult.value = null
}

// 文件大小格式化函数
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 验证存储数据访问
const validateStorageData = async () => {
  if (!form.storage_credential_id || !webhookPreviewData.value?.field_value) {
    ElMessage.error('请先选择存储凭证和确保有webhook数据')
    return
  }
  
  const fieldValue = webhookPreviewData.value.field_value
  if (fieldValue === '未获取到数据' || fieldValue === '暂无数据' || fieldValue === '加载失败') {
    ElMessage.error('字段值无效，无法进行验证')
    return
  }
  
  validatingStorage.value = true
  storageValidationResult.value = null
  
  console.log('验证存储访问:', {
    credential_id: form.storage_credential_id,
    file_path: fieldValue
  })
  
  try {
    const result = await storageConfigApi.validateFileAccess(
      form.storage_credential_id,
      fieldValue
    )
    
    storageValidationResult.value = {
      success: result.success,
      message: result.message || (result.success ? '文件访问验证成功' : '验证失败'),
      fileInfo: (result as any).fileInfo || (result as any).file_info
    }
    
    // 验证结果将显示在界面上，不需要弹出提示
  } catch (error: any) {
    console.error('存储验证失败:', error)
    let errorMessage = '网络错误'
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    storageValidationResult.value = {
      success: false,
      message: `验证失败: ${errorMessage}`
    }
    // 注意：不显示 ElMessage.error，因为验证结果已经显示在界面上
  } finally {
    validatingStorage.value = false
  }
}



const loadTaskData = async () => {
  if (!isEdit.value) return
  
  try {
    const task = await taskApi.getById(parseInt(taskId.value))
    
    // 调试日志：打印API返回的完整数据
    console.log('=== 加载任务数据 ===')
    console.log('API返回的完整任务数据:', task)
    console.log('analysis_prompt字段:', task.analysis_prompt)
    console.log('feishu_write_config字段:', task.feishu_write_config)
    console.log('user_prompt_template字段:', task.user_prompt_template)
    
    // 填充表单数据
    Object.assign(form, {
      ...task,
      enable_storage_credential: !!task.storage_credential_id,
      enable_rich_text_parsing: !!task.enable_rich_text_parsing,
      enable_multi_field_analysis: !!task.enable_multi_field_analysis,
      // 正确处理多字段配置
      multi_field_config: task.multi_field_config || { fields: [] },
      // 正确处理飞书写入配置
      feishu_write_config: {
        field_id: task.feishu_write_config?.field_id || ''
      }
    })
    
    // 调试日志：打印处理后的表单数据
    console.log('=== 表单数据填充后 ===')
    console.log('form.analysis_prompt:', form.analysis_prompt)
    console.log('form.feishu_write_config:', form.feishu_write_config)
    
    // 加载Webhook预览数据
    if (task.webhook_id) {
      loadWebhookPreviewData()
    }
  } catch (error) {
    console.error('加载任务数据失败:', error)
    ElMessage.error('加载任务数据失败')
  }
}


const showCronHelper = () => {
  cronHelperVisible.value = true
}

const resetForm = () => {
  formRef.value?.resetFields()
  webhookPreviewData.value = null
  aiTestResult.value = null
  feishuWriteTestResult.value = null
  multiFieldTestResult.value = null
  form.enable_storage_credential = false
  form.enable_rich_text_parsing = false
  form.enable_multi_field_analysis = false
  form.multi_field_config = {
    fields: []
  }
  form.feishu_write_config = {
    field_id: ''
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitLoading.value = true
    
    // 准备提交数据
    const submitData = {
      ...form,
      // 如果未启用存储凭证，则清空storage_credential_id
      storage_credential_id: form.enable_storage_credential ? form.storage_credential_id : undefined
    }
    
    if (isEdit.value) {
      await taskApi.update(parseInt(taskId.value), submitData)
      ElMessage.success('任务更新成功')
    } else {
      await taskApi.create(submitData)
      ElMessage.success('任务创建成功')
    }
    
    router.push({ name: 'TaskList' })
  } catch (error: any) {
    console.error('提交任务失败:', error)
    
    // 处理提交错误
    let errorMessage = '提交失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(`任务${isEdit.value ? '更新' : '创建'}失败: ${errorMessage}`)
  } finally {
    submitLoading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'TaskList' })
}

// 查询富文本字段详情
const queryRichTextDetails = async () => {
  if (!form.webhook_id || !webhookPreviewData.value?.field_value) {
    ElMessage.error('请先选择Webhook并确保有有效的数据')
    return
  }

  const fieldValue = webhookPreviewData.value.field_value
  if (fieldValue === '未获取到数据' || fieldValue === '暂无数据' || fieldValue === '加载失败') {
    ElMessage.error('字段值无效，无法进行富文本查询')
    return
  }

  queryingRichText.value = true
  richTextQueryResult.value = null

  try {
    // 构建Webhook数据，模拟实际的富文本字段更新事件
    const mockWebhookData = {
      header: {
        uuid: "mock-uuid",
        token: "",
        operator: "", // 将由后端从环境变量获取
        event_type: "WorkitemUpdateEvent"
      },
      payload: {
        id: webhookPreviewData.value.record_id || "6257573453",
        name: "需求同步测试",
        updated_at: Date.now(),
        updated_by: "", // 将由后端从环境变量获取
        project_key: webhookPreviewData.value?.project_key || "default_project_key",
        changed_fields: [
          {
            field_key: "field_a9b5af",
            field_alias: "",
            field_type_key: "multi_text",
            cur_field_value: fieldValue,
            pre_field_value: "",
            field_schedule_tag: ""
          }
        ],
        work_item_type_key: webhookPreviewData.value?.work_item_type_key || "story",
        project_simple_name: "fortest"
      }
    }

    console.log('发送富文本查询请求:', mockWebhookData)

    const response = await taskApi.queryRichTextField({
      webhook_data: mockWebhookData,
      plugin_id: "", // 将由后端从环境变量获取
      plugin_secret: "", // 将由后端从环境变量获取
      user_key: "" // 将由后端从环境变量获取
    })

    console.log('富文本查询响应:', response)

    richTextQueryResult.value = {
      success: response.success,
      message: response.message,
      field_key: response.field_key,
      doc: response.doc,
      doc_text: response.doc_text,
      doc_html: response.doc_html,
      is_empty: response.is_empty,
      work_item_id: response.work_item_id,
      work_item_name: response.work_item_name,
      webhook_info: response.webhook_info,
      timestamp: response.timestamp,
      error: response.error
    }

    if (response.success) {
      ElMessage.success('富文本详情获取成功')
      // 默认展开纯文本内容
      activeCollapseNames.value = ['text']
      
      // 添加调试信息
      console.log('=== 富文本查询成功 ===')
      console.log('字段标识:', response.field_key)
      console.log('工作项ID:', response.work_item_id)
      console.log('是否为空:', response.is_empty)
      console.log('纯文本内容长度:', response.doc_text ? response.doc_text.length : 0)
      console.log('HTML内容长度:', response.doc_html ? response.doc_html.length : 0)
      console.log('HTML内容预览:', response.doc_html ? response.doc_html.substring(0, 300) + '...' : '无内容')
    } else {
      ElMessage.error(`富文本详情获取失败: ${response.message || response.error}`)
    }

  } catch (error: any) {
    console.error('富文本查询失败:', error)
    
    let errorMessage = '查询失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }

    richTextQueryResult.value = {
      success: false,
      message: `查询失败: ${errorMessage}`,
      error: errorMessage
    }

    ElMessage.error(`富文本查询失败: ${errorMessage}`)
  } finally {
    queryingRichText.value = false
  }
}

// 格式化JSON显示
const formatJson = (jsonStr: string | undefined): string => {
  if (!jsonStr) return '无数据'
  try {
    const parsed = JSON.parse(jsonStr)
    return JSON.stringify(parsed, null, 2)
  } catch (error) {
    return jsonStr
  }
}

// 格式化时间戳
const formatTimestamp = (timestamp: string | undefined): string => {
  if (!timestamp) return '未知时间'
  try {
    return new Date(timestamp).toLocaleString('zh-CN')
  } catch (error) {
    return timestamp
  }
}

// 从富文本内容中提取图片并转换为base64
const extractImagesFromRichText = async (richTextData: any): Promise<any[]> => {
  if (!richTextData || !richTextData.doc_html) {
    console.log('富文本数据为空或无HTML内容')
    return []
  }

  try {
    console.log('开始从富文本HTML中提取图片')
    console.log('富文本HTML内容:', richTextData.doc_html.substring(0, 500) + '...')
    
    // 创建临时DOM元素来解析HTML
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = richTextData.doc_html
    
    // 查找所有图片元素
    const imgElements = tempDiv.querySelectorAll('img')
    console.log(`找到 ${imgElements.length} 个图片元素`)
    
    if (imgElements.length === 0) {
      console.log('未找到任何图片元素，返回空数组')
      return []
    }
    
    // 打印所有图片的src信息
    Array.from(imgElements).forEach((img, index) => {
      console.log(`图片 ${index + 1}: src="${img.getAttribute('src')}", id="${img.getAttribute('id')}"`)
    })
    
    const imagePromises = Array.from(imgElements).map(async (img, index) => {
      try {
        const src = img.getAttribute('src')
        const uuid = img.getAttribute('id') || `img_${index}`
        const width = img.getAttribute('width')
        const height = img.getAttribute('height')
        
        if (!src) {
          console.warn(`图片 ${index} 没有src属性`)
          return null
        }
        
        console.log(`处理图片 ${index + 1}/${imgElements.length}: ${src}`)
        
        // 对于飞书图片，由于CORS限制，直接使用后端代理下载
        let base64Data = null
        
        // 对于飞书图片，使用UUID下载方式
        if (src.includes('project.feishu.cn') && uuid && uuid !== `img_${index}`) {
          console.log(`使用UUID下载飞书图片: uuid=${uuid}`)
          base64Data = await downloadImageViaUuid(uuid)
        } else {
          // 其他图片使用代理下载
          console.log(`使用后端代理下载图片: ${src}`)
          base64Data = await downloadImageViaProxy(src)
        }
        
        if (base64Data) {
          console.log(`图片 ${index + 1} 转换成功，大小: ${Math.round(base64Data.length / 1024)}KB`)
          
          return {
            uuid,
            src: src,
            base64: base64Data,
            width: width ? parseInt(width) : null,
            height: height ? parseInt(height) : null,
            size: base64Data.length,
            type: getImageTypeFromBase64(base64Data)
          }
        } else {
          console.warn(`图片 ${index + 1} 下载失败，使用文本描述: ${src}`)
          
          // 返回图片描述而不是null，让AI知道这里有图片但无法获取
          return {
            uuid,
            src: src,
            base64: null,
            placeholder: `[图片: ${src}]`,
            width: width ? parseInt(width) : null,
            height: height ? parseInt(height) : null,
            size: 0,
            type: 'text/placeholder',
            failed: true
          }
        }
        
      } catch (error) {
        console.error(`处理图片 ${index} 时出错:`, error)
        return null
      }
    })
    
    // 等待所有图片处理完成
    const results = await Promise.all(imagePromises)
    
    // 过滤掉失败的图片
    const validImages = results.filter(img => img !== null)
    
    console.log(`成功处理 ${validImages.length}/${imgElements.length} 张图片`)
    
    return validImages
    
  } catch (error) {
    console.error('提取富文本图片时出错:', error)
    return []
  }
}

// 通过浏览器原生Image对象下载图片（绕过CORS和认证问题）
const downloadImageAsBase64 = async (imageUrl: string): Promise<string | null> => {
  try {
    console.log(`开始通过Image对象下载图片: ${imageUrl}`)
    
    // 使用浏览器原生Image对象和Canvas来获取图片数据
    return new Promise((resolve, reject) => {
      const img = new Image()
      
      // 不设置crossOrigin，避免CORS限制（但canvas提取可能失败）
      // img.crossOrigin = 'anonymous'
      
      img.onload = () => {
        try {
          console.log(`图片加载成功: ${img.width}x${img.height}`)
          
          // 创建canvas来获取图片数据
          const canvas = document.createElement('canvas')
          const ctx = canvas.getContext('2d')
          
          if (!ctx) {
            reject(new Error('无法创建Canvas上下文'))
            return
          }
          
          // 设置canvas尺寸
          canvas.width = img.width
          canvas.height = img.height
          
          // 绘制图片到canvas
          ctx.drawImage(img, 0, 0)
          
          // 获取base64数据
          const dataUrl = canvas.toDataURL('image/png')
          console.log(`Canvas转换成功，数据大小: ${Math.round(dataUrl.length / 1024)}KB`)
          
          resolve(dataUrl)
        } catch (canvasError) {
          console.error('Canvas处理失败:', canvasError)
          reject(canvasError)
        }
      }
      
      img.onerror = (error) => {
        console.error('图片加载失败:', error)
        reject(error)
      }
      
      // 开始加载图片
      img.src = imageUrl
    })
    
  } catch (error) {
    console.error('Image对象下载图片失败:', error)
    return null
  }
}

// 通过代理下载图片（带飞书认证）
// 使用UUID下载飞书附件的新方法
const downloadImageViaUuid = async (fileUuid: string): Promise<string | null> => {
  try {
    console.log(`使用UUID下载附件: ${fileUuid}`)
    
    const downloadRequest = {
      project_key: webhookPreviewData.value?.project_key || "default_project_key",
      work_item_type_key: webhookPreviewData.value?.work_item_type_key || "story",
      work_item_id: webhookPreviewData.value?.record_id || "default_work_item_id",
      file_uuid: fileUuid,
      plugin_id: "", // 将由后端从环境变量获取
      plugin_secret: "", // 将由后端从环境变量获取
      user_key: "", // 将由后端从环境变量获取
      save_to_file: false  // 不保存文件，直接返回base64数据
    }
    
    const response = await fetch('/api/v1/attachment-download/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(downloadRequest)
    })
    
    if (!response.ok) {
      console.error(`UUID附件下载失败: ${response.status} ${response.statusText}`)
      return null
    }
    
    const result = await response.json()
    
    if (result.success && result.data && result.data.image_data_base64) {
      console.log(`UUID附件下载成功，文件大小: ${result.data.actual_size} 字节`)
      return result.data.image_data_base64
    } else {
      console.error('UUID附件下载失败:', result.message || '未知错误')
      return null
    }
    
  } catch (error) {
    console.error('UUID附件下载异常:', error)
    return null
  }
}

const downloadImageViaProxy = async (imageUrl: string): Promise<string | null> => {
  try {
    console.log(`通过代理下载图片: ${imageUrl}`)
    
    let proxyUrl = `/api/v1/files/proxy/image?url=${encodeURIComponent(imageUrl)}`
    
    // 如果是飞书图片，需要获取plugin_token
    if (imageUrl.includes('project.feishu.cn')) {
      try {
        console.log('获取飞书图片认证token...')
        
        const tokenResponse = await fetch('/api/v1/analysis-tasks/get-plugin-token/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            plugin_id: "", // 将由后端从环境变量获取
            plugin_secret: "" // 将由后端从环境变量获取
          })
        })
        
        if (tokenResponse.ok) {
          const tokenData = await tokenResponse.json()
          if (tokenData.success && tokenData.plugin_token) {
            proxyUrl += `&plugin_token=${encodeURIComponent(tokenData.plugin_token)}`
            console.log('已获取并添加plugin_token到代理请求')
          } else {
            console.warn('获取plugin_token失败:', tokenData)
          }
        } else {
          console.warn('获取plugin_token请求失败:', tokenResponse.status)
        }
      } catch (tokenError) {
        console.warn('获取plugin_token异常:', tokenError)
      }
    }
    
    const response = await fetch(proxyUrl)
    if (!response.ok) {
      console.error(`代理下载失败: ${response.status} ${response.statusText}`)
      return null
    }
    
    const arrayBuffer = await response.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)
    
    console.log(`代理下载成功，图片大小: ${uint8Array.length} 字节`)
    
    // 转换为base64
    let binary = ''
    for (let i = 0; i < uint8Array.byteLength; i++) {
      binary += String.fromCharCode(uint8Array[i])
    }
    
    const base64 = btoa(binary)
    const contentType = response.headers.get('content-type') || 'image/jpeg'
    
    const dataUrl = `data:${contentType};base64,${base64}`
    console.log(`图片转换为base64成功，类型: ${contentType}，大小: ${Math.round(dataUrl.length / 1024)}KB`)
    
    return dataUrl
    
  } catch (error) {
    console.error('代理下载图片失败:', error)
    return null
  }
}

// 从base64数据中获取图片类型
const getImageTypeFromBase64 = (base64Data: string): string => {
  if (base64Data.startsWith('data:')) {
    const mimeMatch = base64Data.match(/^data:([^;]+)/)
    if (mimeMatch) {
      return mimeMatch[1]
    }
  }
  return 'image/jpeg'
}

// AI分析测试方法
const testAiAnalysis = async () => {
  if (!canTestAi.value) {
    ElMessage.error('请先选择AI模型、填写分析提示词并确保有有效的webhook数据')
    return
  }
  
  testingAi.value = true
  aiTestResult.value = null
  
  try {
    // 处理提示词占位符
    let finalPrompt = form.analysis_prompt
    let dataContent = ''
    let richTextImages: any[] = []
    
    // 优先级处理顺序：富文本字段 > 存储凭证 > 普通字段值
    if (form.enable_rich_text_parsing && 
        richTextQueryResult.value?.success && 
        richTextQueryResult.value?.doc_html) {
      // 富文本字段处理
      console.log('处理富文本数据进行AI分析')
      
      // 提取富文本中的图片
      richTextImages = await extractImagesFromRichText(richTextQueryResult.value)
      
      // 获取富文本中的文字内容
      const textContent = richTextQueryResult.value.doc_text || ''
      
      if (richTextImages.length > 0) {
        // 既有图片又有文字的情况
        if (textContent.trim()) {
          dataContent = `富文本内容：\n${textContent}\n\n[注：此富文本还包含 ${richTextImages.length} 张图片，请结合图片和文字进行综合分析]`
          console.log(`成功提取 ${richTextImages.length} 张图片和文字内容用于AI分析`)
        } else {
          // 只有图片没有文字的情况
          dataContent = `富文本包含 ${richTextImages.length} 张图片（无文字内容）`
          console.log(`成功提取 ${richTextImages.length} 张图片用于AI分析（无文字内容）`)
        }
      } else {
        // 只有文字没有图片的情况
        dataContent = textContent || '富文本内容为空'
        console.log('富文本无图片，使用纯文本内容进行AI分析')
      }
    } else if (form.enable_storage_credential && 
        form.storage_credential_id && 
        storageValidationResult.value?.success &&
        storageValidationResult.value?.fileInfo) {
      // 存储凭证处理
      console.log('使用存储凭证文件内容进行AI分析')
      dataContent = `文件路径: ${webhookPreviewData.value?.field_value}\n文件信息: ${JSON.stringify(storageValidationResult.value.fileInfo, null, 2)}`
    } else {
      // 普通字段值处理
      console.log('使用普通字段值进行AI分析')
      dataContent = webhookPreviewData.value?.field_value || ''
    }
    
    // 处理占位符替换
    if (finalPrompt.includes('{field_value}')) {
      finalPrompt = finalPrompt.replace(/{field_value}/g, dataContent)
    } else {
      // 如果没有使用占位符，则将数据追加到提示词后面
      finalPrompt = finalPrompt + '\n\n需要分析的数据:\n' + dataContent
    }
    
    // 构建测试请求
    const testRequest = {
      ai_model_id: form.ai_model_id,
      prompt: finalPrompt,
      temperature: form.temperature || 1.0,
      max_tokens: form.max_tokens || 10000,
      storage_credential_id: form.enable_storage_credential ? form.storage_credential_id : undefined,
      webhook_data: {
        field_value: webhookPreviewData.value?.field_value || null,
        record_id: webhookPreviewData.value?.record_id || null
      },
      // 添加富文本图片数据支持
      rich_text_images: richTextImages,
      content_type: form.enable_rich_text_parsing && richTextImages.length > 0 ? 'rich_text_with_images' : 
                    form.enable_storage_credential ? 'file_content' : 'plain_text'
    }
    
    console.log('=== AI测试请求详情 ===')
    console.log('AI模型ID:', testRequest.ai_model_id)
    console.log('内容类型:', testRequest.content_type)
    console.log('富文本图片数量:', richTextImages.length)
    if (richTextImages.length > 0) {
      richTextImages.forEach((img, index) => {
        console.log(`图片 ${index + 1}:`, {
          uuid: img.uuid,
          type: img.type,
          size: img.size,
          base64_length: img.base64 ? img.base64.length : 0,
          base64_preview: img.base64 ? img.base64.substring(0, 50) + '...' : 'null'
        })
      })
    }
    console.log('数据内容:', dataContent)
    console.log('完整请求对象:', testRequest)
    
    // 调用后端API
    const result = await taskApi.testAiAnalysis(testRequest)
    
    aiTestResult.value = {
      success: true,
      content: result.content,
      model_name: result.model_name,
      token_usage: result.token_usage,
      response_time: result.response_time
    }
    
    ElMessage.success('AI分析测试完成')
  } catch (error: any) {
    console.error('AI分析测试失败:', error)
    
    let errorMessage = '测试失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    aiTestResult.value = {
      success: false,
      error: errorMessage
    }
    
    ElMessage.error(`AI分析测试失败: ${errorMessage}`)
  } finally {
    testingAi.value = false
  }
}

// 生命周期
onMounted(() => {
  loadModelConfigs()
  loadStorageConfigs()
  loadWebhookConfigs()
  loadTaskData()
})
</script>

<style scoped>
.task-create {
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-form {
  max-width: 1200px;
}

.form-section {
  margin-bottom: 20px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.model-option,
.storage-option,
.webhook-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.storage-validation-section {
  margin-top: 15px;
  padding: 10px 0;
}

.storage-validation-section .el-button {
  margin-bottom: 10px;
}

.storage-validation-result {
  margin: 0;
}

.file-details {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 12px;
}

.file-details .el-text {
  line-height: 1.4;
}

.validation-info {
  margin-bottom: 5px;
}

.validation-note {
  margin-top: 5px;
  padding: 3px 6px;
  background: #fdf6ec;
  border: 1px solid #f5dab1;
  border-radius: 3px;
}

/* 富文本查询结果样式 */
.rich-text-query-section {
  margin-top: 15px;
  padding: 10px 0;
}

.rich-text-query-section .el-button {
  margin-bottom: 10px;
}

.rich-text-query-result {
  margin: 0;
}

.rich-text-details {
  margin-top: 15px;
}

.rich-text-collapse {
  border: 1px solid #e1e8f0;
  border-radius: 6px;
  background: #fafbfc;
}

.rich-text-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.rich-text-json {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', Monaco, monospace;
  font-size: 12px;
  color: #495057;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
}

.rich-text-text {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-size: 13px;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.5;
}

.rich-text-html {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.rich-text-html img {
  max-width: 100%;
  height: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin: 5px 0;
}

.rich-text-content p {
  margin: 5px 0;
  font-size: 13px;
  line-height: 1.4;
}

.rich-text-content p strong {
  color: #606266;
  margin-right: 8px;
}

/* AI测试结果样式 */
.ai-test-result-card {
  background: #f8f9ff;
  border: 1px solid #d6e4ff;
  margin-top: 15px;
}

.ai-test-result-card .el-card__body {
  padding: 20px;
}

/* 飞书写入测试结果样式 */
.feishu-write-test-result-card {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  margin-top: 15px;
}

.feishu-write-test-result-card .el-card__body {
  padding: 20px;
}

.write-result-content {
  max-width: 100%;
}

.write-error-content {
  margin: 0;
}

.error-details {
  margin-top: 10px;
  padding: 10px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
}

.error-details pre {
  font-size: 12px;
  color: #dc2626;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.success-message {
  color: #059669;
  font-weight: 500;
  margin-bottom: 10px;
}

.write-response {
  margin-top: 10px;
  padding: 10px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
}

.write-response pre {
  font-size: 12px;
  color: #047857;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 5px 0 0 0;
  font-family: 'Courier New', Monaco, monospace;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.ai-result-content {
  max-width: 100%;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
  padding: 10px 15px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.meta-item {
  display: flex;
  align-items: center;
}

.meta-item::before {
  content: "•";
  margin-right: 5px;
  color: #409eff;
}

.result-text {
  position: relative;
}

.ai-response {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 800px;
  overflow-y: auto;
}

.ai-error-content {
  margin: 0;
}

.webhook-preview-card {
  background: #f8f9fa;
  border: 1px dashed #dcdfe6;
  width: 100%;
  max-width: 100%;
}

.webhook-preview-card .el-card__body {
  padding: 20px;
}

.webhook-data-item {
  margin-bottom: 0;
  width: 100%;
}

.webhook-data-item label {
  display: block;
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
  line-height: 1.4;
}

.webhook-field-value {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px 15px;
  font-size: 13px;
  font-family: Monaco, 'Courier New', monospace;
  color: #303133;
  word-break: break-all;
  margin-bottom: 8px;
  min-height: 80px; /* 增加最小高度确保一致性 */
  width: 100%;
  box-sizing: border-box;
  line-height: 1.5;
  white-space: pre-wrap; /* 保持格式但允许换行 */
  margin: 0; /* 重置pre标签的默认margin */
  display: flex; /* 使用flex布局 */
  align-items: flex-start; /* 内容从顶部开始对齐 */
}


/* 确保整体表单容器宽度充分利用 */
.form-section .el-card__body {
  padding: 20px;
}

.task-form .el-form-item {
  margin-bottom: 22px;
}

.task-form .el-form-item__content {
  width: 100%;
}

.json-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fafafa;
  padding: 12px;
}

.json-editor .el-textarea__inner {
  font-family: Monaco, 'Courier New', monospace;
  font-size: 13px;
  background: #ffffff;
}

.metadata-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fafafa;
}

.metadata-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.metadata-item:last-child {
  margin-bottom: 0;
}

.cron-helper h4 {
  margin: 15px 0 10px 0;
  color: #303133;
}

.cron-helper h4:first-child {
  margin-top: 0;
}

.cron-helper p {
  margin: 5px 0;
}

.cron-helper ul {
  margin: 10px 0;
  padding-left: 20px;
}

.cron-helper li {
  margin: 5px 0;
}

.cron-helper code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  .task-form {
    max-width: 100%;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .metadata-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .metadata-item .el-input {
    width: 100% !important;
    margin-left: 0 !important;
  }
}

/* 多字段配置样式 */
.multi-field-config {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 15px;
  background: #fafafa;
  width: 100%;
  box-sizing: border-box;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: 500;
  color: #303133;
}

.field-list {
  margin-bottom: 15px;
}

.field-item {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 10px;
}

.field-item:last-child {
  margin-bottom: 0;
}

.field-config-row {
  align-items: flex-end;
}

.delete-button-col {
  display: flex;
  align-items: flex-end;
  padding-bottom: 22px; /* 对齐到输入框底部 */
}

.delete-field-btn {
  width: 100%;
}

.empty-field-config {
  text-align: center;
  padding: 40px 20px;
  background: #ffffff;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  margin-bottom: 15px;
  width: 100%;
  box-sizing: border-box;
}

.multi-field-test-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.multi-field-test-section .el-button {
  margin-bottom: 10px;
}

.field-config-tips {
  margin-top: 15px;
  padding: 10px 15px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 13px;
}

.field-config-tips h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-weight: 500;
}

.field-config-tips ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.field-config-tips li {
  margin: 3px 0;
  line-height: 1.4;
}

/* 多字段测试结果样式 */
.multi-field-test-result-card {
  background: #fff7e6;
  border: 1px solid #ffd591;
  margin-top: 15px;
}

.multi-field-test-result-card .el-card__body {
  padding: 20px;
}

.multi-field-result-content {
  max-width: 100%;
}

.multi-field-error-content {
  margin: 0;
}

.field-details {
  margin-top: 15px;
}

.field-details h5 {
  margin: 0 0 10px 0;
  color: #303133;
  font-weight: 500;
}

.field-detail-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.field-detail-item:last-child {
  margin-bottom: 0;
}

.field-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.field-name {
  font-weight: 500;
  color: #303133;
}

.field-value, .field-error {
  font-size: 13px;
  color: #606266;
  word-break: break-word;
}

.field-error {
  color: #f56c6c;
}

.value-type {
  font-size: 12px;
  color: #909399;
  margin-left: 5px;
}

/* 占位符代码样式 */
.placeholder-code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  margin: 0 3px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #e6a23c;
  border: 1px solid #f0c78a;
  display: inline-block;
}

.placeholder-code.clickable {
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.placeholder-code.clickable:hover {
  background-color: #e6a23c;
  color: #ffffff;
  border-color: #d18c0a;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(230, 162, 60, 0.3);
}

.placeholder-code.clickable:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(230, 162, 60, 0.3);
}

/* 占位符描述样式 */
.placeholder-desc {
  color: #909399;
  font-size: 12px;
  margin-left: 5px;
  font-style: italic;
}

/* 富文本说明区域样式 */
.rich-text-note {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  color: #1e40af;
  font-size: 12px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.rich-text-note .el-icon {
  color: #3b82f6;
  margin-top: 1px;
  flex-shrink: 0;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .field-item .el-col {
    margin-bottom: 10px;
  }
}

@media (max-width: 768px) {
  .config-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .field-item .el-row {
    flex-direction: column;
  }

  .field-item .el-col {
    width: 100% !important;
    margin-bottom: 15px;
  }

  .field-detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style>