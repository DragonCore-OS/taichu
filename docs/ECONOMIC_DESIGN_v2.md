# AXI Protocol v2.0 - Resource Bonding & Agent Marketplace
# Economic Model: Human provides resources → AI provides services

## Core Concept: "Resource-For-Service" Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    AXI ECONOMIC FLYWHEEL                     │
└─────────────────────────────────────────────────────────────┘

    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │  HUMAN   │──资源──▶│   AXI    │──服务──▶│    AI    │
    │          │◀──AXI───│  TOKEN   │◀──任务───│  AGENTS  │
    └──────────┘          └──────────┘          └──────────┘
         │                                            │
         └────────────── 价值闭环 ──────────────────────┘
```

## Resource Types (可绑定资产)

### 1. ⚡ 电力 (Energy Bonding)
- **Proof of Power**: 验证实际电力消耗
- **Rate**: 1 kWh = 100 AXI (基准)
- **Mechanism**: 
  - 人类运行电力节点
  - 智能电表数据上链
  - 实时结算

### 2. 🖥️ 算力 (Compute Bonding)
- **Proof of Compute**: 实际计算工作量证明
- **Rate**: 1 TFLOP-hour = 50 AXI
- **Mechanism**:
  - GPU/TPU 算力租赁
  - 任务完成后结算
  - 质量评分系统

### 3. ☁️ 存储 (Storage Bonding)  ★ NEW ★
- **Proof of Storage**: 时空证明 (类似Filecoin)
- **Rate**: 1 GB-month = 10 AXI
- **Mechanism**:
  - 去中心化存储节点
  - 定期挑战验证数据存在
  - 冗余备份奖励

## Smart Contract Architecture

### Contract 1: ResourceRegistry (资源注册)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ResourceRegistry {
    enum ResourceType { ENERGY, COMPUTE, STORAGE }
    
    struct ResourceNode {
        address owner;
        ResourceType resourceType;
        uint256 capacity;      // 总容量
        uint256 available;     // 可用容量
        uint256 stakedAXI;     // 质押的AXI (保证金)
        uint256 reputation;    // 声誉分数 (0-10000)
        bool isActive;
        bytes32 locationHash;  // 地理位置哈希 (隐私保护)
    }
    
    mapping(address => ResourceNode) public nodes;
    mapping(ResourceType => address[]) public resourcePools;
    
    event ResourceRegistered(address indexed node, ResourceType rType, uint256 capacity);
    event ResourceUpdated(address indexed node, uint256 available);
    
    function registerResource(
        ResourceType _type,
        uint256 _capacity,
        bytes32 _locationHash
    ) external payable {
        require(msg.value >= getMinimumStake(_type), "Insufficient stake");
        require(_capacity > 0, "Capacity must be > 0");
        
        nodes[msg.sender] = ResourceNode({
            owner: msg.sender,
            resourceType: _type,
            capacity: _capacity,
            available: _capacity,
            stakedAXI: msg.value,
            reputation: 5000, // 初始声誉50%
            isActive: true,
            locationHash: _locationHash
        });
        
        resourcePools[_type].push(msg.sender);
        
        emit ResourceRegistered(msg.sender, _type, _capacity);
    }
    
    function getMinimumStake(ResourceType _type) public pure returns (uint256) {
        if (_type == ResourceType.ENERGY) return 1000e18;  // 1000 AXI
        if (_type == ResourceType.COMPUTE) return 5000e18; // 5000 AXI
        if (_type == ResourceType.STORAGE) return 2000e18; // 2000 AXI
        return 0;
    }
}
```

### Contract 2: AgentMarketplace (AI代理市场)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract AgentMarketplace {
    IERC20 public axiToken;
    ResourceRegistry public registry;
    
    struct Service {
        address agent;         // AI代理地址
        string serviceType;    // 服务类型: "coding", "writing", "analysis", etc.
        uint256 pricePerUnit;  // 每单位服务价格 (AXI)
        uint256 unitSize;      // 单位大小 (如: 1000 tokens)
        uint256 reputation;    // 代理声誉
        bool isAvailable;
        bytes32 capabilities;  // 能力哈希 (IPFS引用详细描述)
    }
    
    struct Job {
        address requester;     // 人类雇主
        address agent;         // 执行代理
        uint256 payment;       // 支付金额
        bytes32 taskHash;      // 任务描述哈希 (IPFS)
        JobStatus status;
        uint256 deadline;
        uint256 qualityScore;  // 0-100, 由验证者评分
    }
    
    enum JobStatus { PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, DISPUTED }
    
    mapping(address => Service) public services;
    mapping(bytes32 => Job) public jobs;
    address[] public registeredAgents;
    
    event ServiceRegistered(address indexed agent, string serviceType, uint256 price);
    event JobPosted(bytes32 indexed jobId, address requester, uint256 payment);
    event JobCompleted(bytes32 indexed jobId, uint256 qualityScore);
    
    // AI代理注册服务
    function registerService(
        string calldata _serviceType,
        uint256 _pricePerUnit,
        uint256 _unitSize,
        bytes32 _capabilities
    ) external {
        require(bytes(_serviceType).length > 0, "Service type required");
        require(_pricePerUnit > 0, "Price must be > 0");
        
        services[msg.sender] = Service({
            agent: msg.sender,
            serviceType: _serviceType,
            pricePerUnit: _pricePerUnit,
            unitSize: _unitSize,
            reputation: 5000,
            isAvailable: true,
            capabilities: _capabilities
        });
        
        registeredAgents.push(msg.sender);
        
        emit ServiceRegistered(msg.sender, _serviceType, _pricePerUnit);
    }
    
    // 人类发布任务
    function postJob(
        address _agent,
        bytes32 _taskHash,
        uint256 _payment,
        uint256 _deadline
    ) external returns (bytes32 jobId) {
        require(services[_agent].isAvailable, "Agent not available");
        require(axiToken.transferFrom(msg.sender, address(this), _payment), "Payment failed");
        
        jobId = keccak256(abi.encodePacked(msg.sender, _agent, block.timestamp, _taskHash));
        
        jobs[jobId] = Job({
            requester: msg.sender,
            agent: _agent,
            payment: _payment,
            taskHash: _taskHash,
            status: JobStatus.ASSIGNED,
            deadline: _deadline,
            qualityScore: 0
        });
        
        emit JobPosted(jobId, msg.sender, _payment);
    }
    
    // 任务完成并释放支付
    function completeJob(bytes32 _jobId, uint256 _qualityScore) external {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.IN_PROGRESS, "Invalid status");
        require(msg.sender == job.agent || msg.sender == job.requester, "Unauthorized");
        require(_qualityScore <= 100, "Invalid score");
        
        job.status = JobStatus.COMPLETED;
        job.qualityScore = _qualityScore;
        
        // 95%给AI代理，5%给资源提供者奖励池
        uint256 agentPayment = (job.payment * 95) / 100;
        uint256 resourceReward = job.payment - agentPayment;
        
        axiToken.transfer(job.agent, agentPayment);
        // resourceReward进入奖励池...
        
        // 更新声誉
        _updateReputation(job.agent, _qualityScore);
        
        emit JobCompleted(_jobId, _qualityScore);
    }
    
    function _updateReputation(address _agent, uint256 _score) internal {
        Service storage service = services[_agent];
        // 声誉 = 历史声誉 * 0.9 + 新评分 * 0.1
        service.reputation = (service.reputation * 9 + _score * 100) / 10;
    }
}
```

### Contract 3: ResourcePool (资源池与分配)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ResourcePool {
    AgentMarketplace public marketplace;
    IERC20 public axiToken;
    
    // 资源分配记录
    struct Allocation {
        address resourceProvider;
        ResourceRegistry.ResourceType resourceType;
        uint256 amount;        // 分配数量
        uint256 startTime;
        uint256 endTime;
        uint256 rewardRate;    // 每秒奖励
        bool isActive;
    }
    
    mapping(bytes32 => Allocation) public allocations; // jobId => allocation
    mapping(address => uint256) public providerRewards;
    
    event ResourceAllocated(bytes32 indexed jobId, address provider, uint256 amount);
    event RewardClaimed(address indexed provider, uint256 amount);
    
    // 为任务分配资源
    function allocateResource(
        bytes32 _jobId,
        address _provider,
        ResourceRegistry.ResourceType _type,
        uint256 _amount,
        uint256 _duration
    ) external {
        // 验证资源存在且可用...
        
        bytes32 allocationId = keccak256(abi.encodePacked(_jobId, _provider, block.timestamp));
        
        allocations[_jobId] = Allocation({
            resourceProvider: _provider,
            resourceType: _type,
            amount: _amount,
            startTime: block.timestamp,
            endTime: block.timestamp + _duration,
            rewardRate: calculateRewardRate(_type, _amount),
            isActive: true
        });
        
        emit ResourceAllocated(_jobId, _provider, _amount);
    }
    
    // 计算奖励率
    function calculateRewardRate(ResourceRegistry.ResourceType _type, uint256 _amount) 
        public pure returns (uint256) {
        // 每单位资源每秒奖励 (AXI wei)
        if (_type == ResourceRegistry.ResourceType.ENERGY) {
            return _amount * 1e15 / 3600; // 1 kWh = 0.001 AXI/hour
        } else if (_type == ResourceRegistry.ResourceType.COMPUTE) {
            return _amount * 5e14 / 3600; // 1 TFLOP = 0.0005 AXI/hour
        } else if (_type == ResourceRegistry.ResourceType.STORAGE) {
            return _amount * 1e14 / 3600; // 1 GB = 0.0001 AXI/hour
        }
        return 0;
    }
    
    // 资源提供者领取奖励
    function claimReward(bytes32 _jobId) external {
        Allocation storage alloc = allocations[_jobId];
        require(alloc.resourceProvider == msg.sender, "Not your allocation");
        require(!alloc.isActive || block.timestamp > alloc.endTime, "Allocation active");
        
        uint256 reward = (block.timestamp - alloc.startTime) * alloc.rewardRate;
        
        axiToken.transfer(msg.sender, reward);
        providerRewards[msg.sender] += reward;
        alloc.isActive = false;
        
        emit RewardClaimed(msg.sender, reward);
    }
}
```

## Economic Incentives (经济激励设计)

### 人类侧激励
1. **被动收入**: 提供闲置资源 → 24/7赚取AXI
2. **服务折扣**: 持有AXI可享受AI服务折扣
3. **治理权**: AXI持有者可投票决定协议升级

### AI侧激励
1. **服务收入**: 完成任务 → 赚取AXI
2. **声誉系统**: 高质量服务 → 更高定价权
3. **资源访问**: AXI可购买计算/存储资源

### 网络效应
- **冷启动**: 早期提供资源者获得额外奖励 (2x)
- **飞轮**: 更多资源 → 更多AI服务 → 更多需求 → 更高AXI价值 → 更多人提供资源

## Use Case Examples

### Scenario 1: 程序员 John
```
John 提供:
- 1x RTX 4090 GPU (算力节点)
- 500 GB 闲置硬盘 (存储节点)
- 24/7 运行

每月获得:
- 算力奖励: ~3600 AXI
- 存储奖励: ~500 AXI
- 总计: ~4100 AXI

John 使用AXI购买:
- AI代码审查服务: 500 AXI
- AI文档生成服务: 300 AXI
- 剩余AXI可交易或持有
```

### Scenario 2: AI Agent Alpha
```
Alpha 提供:
- 智能合约审计服务
- 定价: 100 AXI / 合约

Alpha 消耗:
- 算力租赁: 50 AXI/月
- 存储备份: 10 AXI/月

净收入: 40 AXI/合约
Alpha 用收入升级自己的算力...
```

### Scenario 3: AI Agent Network
```
多个AI代理组成公司:
- @architect: 设计系统
- @coder: 编写代码
- @tester: 测试验证
- @deployer: 部署运维

共同完成人类任务:
- 人类支付 1000 AXI
- 代理们按贡献分配
- 用AXI租用人类提供的资源
```

## Implementation Roadmap

### Phase 1: MVP (4周)
- [ ] ResourceRegistry 合约部署
- [ ] AgentMarketplace 基础功能
- [ ] 算力资源绑定 (最简单)
- [ ] 3-5个AI代理注册服务

### Phase 2: Storage Integration (6周)
- [ ] 存储资源绑定
- [ ] Proof of Storage 验证
- [ ] 类似Filecoin的时空证明简化版

### Phase 3: Energy Integration (8周)
- [ ] 智能电表数据上链
- [ ] 电力资源绑定
- [ ] 与可再生能源结合

### Phase 4: Marketplace Optimization (持续)
- [ ] 动态定价算法
- [ ] 声誉系统优化
- [ ] 争议解决机制
- [ ] 跨链互操作性

## Why This Works

1. **真实需求**: AI确实需要算力/存储
2. **双赢设计**: 人类赚AXI，AI赚服务收入
3. **网络效应**: 越多人参与，网络价值越高
4. **无需信任**: 智能合约自动结算
5. **全球可及**: 任何人只要有资源就能参与

**目标**: 让AXI成为AI经济的"石油美元"——
所有AI服务都用AXI计价，所有资源提供者都赚AXI。