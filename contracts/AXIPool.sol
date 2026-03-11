// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AXIPool
 * @notice Resource pooling and marketplace for AI agents
 * Human provides: Electricity, Compute, Storage
 * AI provides: Services
 * Exchange medium: AXI Token
 */
contract AXIPool is ReentrancyGuard, Ownable {
    IERC20 public axiToken;
    
    enum ResourceType { ENERGY, COMPUTE, STORAGE }
    
    struct ResourceProvider {
        address owner;
        ResourceType rType;
        uint256 totalCapacity;
        uint256 usedCapacity;
        uint256 stakedAmount;
        uint256 reputation;
        bool isActive;
        uint256 registrationTime;
    }
    
    struct AgentService {
        address agent;
        string serviceType;
        uint256 pricePerUnit;
        uint256 reputation;
        bool isAvailable;
    }
    
    struct Job {
        address requester;
        address agent;
        uint256 payment;
        bytes32 taskHash;
        JobStatus status;
        uint256 createdAt;
        uint256 completedAt;
        uint256 qualityScore;
    }
    
    enum JobStatus { PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED }
    
    // Mappings
    mapping(address => ResourceProvider) public providers;
    mapping(address => AgentService) public agentServices;
    mapping(bytes32 => Job) public jobs;
    mapping(address => uint256) public providerRewards;
    mapping(address => uint256) public agentEarnings;
    
    // Arrays for iteration
    address[] public providerList;
    address[] public agentList;
    bytes32[] public jobList;
    
    // Protocol parameters
    uint256 public platformFee = 500; // 5% (basis points)
    uint256 public minStake = 1000e18; // 1000 AXI
    
    // Events
    event ResourceRegistered(address indexed provider, ResourceType rType, uint256 capacity);
    event AgentRegistered(address indexed agent, string serviceType, uint256 price);
    event JobCreated(bytes32 indexed jobId, address requester, address agent, uint256 payment);
    event JobCompleted(bytes32 indexed jobId, uint256 qualityScore, uint256 payment);
    event RewardClaimed(address indexed provider, uint256 amount);
    
    constructor(address _axiToken) {
        axiToken = IERC20(_axiToken);
    }
    
    /**
     * @notice Register as resource provider (Human)
     */
    function registerResource(
        ResourceType _type,
        uint256 _capacity
    ) external nonReentrant {
        require(_capacity > 0, "Capacity must be > 0");
        require(!providers[msg.sender].isActive, "Already registered");
        
        // Transfer stake
        require(axiToken.transferFrom(msg.sender, address(this), minStake), "Stake failed");
        
        providers[msg.sender] = ResourceProvider({
            owner: msg.sender,
            rType: _type,
            totalCapacity: _capacity,
            usedCapacity: 0,
            stakedAmount: minStake,
            reputation: 5000, // 50% initial
            isActive: true,
            registrationTime: block.timestamp
        });
        
        providerList.push(msg.sender);
        
        emit ResourceRegistered(msg.sender, _type, _capacity);
    }
    
    /**
     * @notice Register as AI agent service provider
     */
    function registerAgentService(
        string calldata _serviceType,
        uint256 _pricePerUnit
    ) external {
        require(_pricePerUnit > 0, "Price must be > 0");
        require(bytes(_serviceType).length > 0, "Service type required");
        
        agentServices[msg.sender] = AgentService({
            agent: msg.sender,
            serviceType: _serviceType,
            pricePerUnit: _pricePerUnit,
            reputation: 5000,
            isAvailable: true
        });
        
        agentList.push(msg.sender);
        
        emit AgentRegistered(msg.sender, _serviceType, _pricePerUnit);
    }
    
    /**
     * @notice Create a job (Human hires AI)
     */
    function createJob(
        address _agent,
        bytes32 _taskHash,
        uint256 _payment
    ) external nonReentrant returns (bytes32 jobId) {
        require(agentServices[_agent].isAvailable, "Agent not available");
        require(_payment > 0, "Payment required");
        
        // Transfer payment from requester
        require(axiToken.transferFrom(msg.sender, address(this), _payment), "Payment failed");
        
        jobId = keccak256(abi.encodePacked(msg.sender, _agent, _taskHash, block.timestamp));
        
        jobs[jobId] = Job({
            requester: msg.sender,
            agent: _agent,
            payment: _payment,
            taskHash: _taskHash,
            status: JobStatus.ASSIGNED,
            createdAt: block.timestamp,
            completedAt: 0,
            qualityScore: 0
        });
        
        jobList.push(jobId);
        
        emit JobCreated(jobId, msg.sender, _agent, _payment);
    }
    
    /**
     * @notice Complete job and distribute payment
     */
    function completeJob(
        bytes32 _jobId,
        uint256 _qualityScore
    ) external nonReentrant {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.ASSIGNED || job.status == JobStatus.IN_PROGRESS, "Invalid status");
        require(msg.sender == job.agent || msg.sender == job.requester, "Unauthorized");
        require(_qualityScore <= 100, "Score 0-100");
        
        job.status = JobStatus.COMPLETED;
        job.completedAt = block.timestamp;
        job.qualityScore = _qualityScore;
        
        // Calculate distributions
        uint256 platformFeeAmount = (job.payment * platformFee) / 10000;
        uint256 resourcePoolAmount = (job.payment * 1000) / 10000; // 10% to resource providers
        uint256 agentPayment = job.payment - platformFeeAmount - resourcePoolAmount;
        
        // Pay agent
        axiToken.transfer(job.agent, agentPayment);
        agentEarnings[job.agent] += agentPayment;
        
        // Update reputations
        _updateAgentReputation(job.agent, _qualityScore);
        
        emit JobCompleted(_jobId, _qualityScore, agentPayment);
    }
    
    /**
     * @notice Resource provider claims accumulated rewards
     */
    function claimProviderReward() external nonReentrant {
        uint256 reward = providerRewards[msg.sender];
        require(reward > 0, "No rewards to claim");
        
        providerRewards[msg.sender] = 0;
        axiToken.transfer(msg.sender, reward);
        
        emit RewardClaimed(msg.sender, reward);
    }
    
    /**
     * @notice Distribute resource pool to providers (called periodically)
     */
    function distributeResourcePool(uint256 _amount) external onlyOwner {
        require(_amount > 0, "Amount required");
        
        uint256 activeProviders = 0;
        for (uint i = 0; i < providerList.length; i++) {
            if (providers[providerList[i]].isActive) {
                activeProviders++;
            }
        }
        
        require(activeProviders > 0, "No active providers");
        
        uint256 rewardPerProvider = _amount / activeProviders;
        
        for (uint i = 0; i < providerList.length; i++) {
            if (providers[providerList[i]].isActive) {
                providerRewards[providerList[i]] += rewardPerProvider;
            }
        }
    }
    
    /**
     * @notice Update agent reputation based on job quality
     */
    function _updateAgentReputation(address _agent, uint256 _score) internal {
        AgentService storage service = agentServices[_agent];
        // Weighted average: 90% history, 10% new score
        service.reputation = (service.reputation * 9 + _score * 100) / 10;
    }
    
    /**
     * @notice Get best available agent for a service type
     */
    function findBestAgent(string calldata _serviceType) external view returns (address) {
        address bestAgent = address(0);
        uint256 bestReputation = 0;
        
        for (uint i = 0; i < agentList.length; i++) {
            AgentService storage service = agentServices[agentList[i]];
            if (service.isAvailable && 
                keccak256(bytes(service.serviceType)) == keccak256(bytes(_serviceType)) &&
                service.reputation > bestReputation) {
                bestAgent = agentList[i];
                bestReputation = service.reputation;
            }
        }
        
        return bestAgent;
    }
    
    // Admin functions
    function setPlatformFee(uint256 _fee) external onlyOwner {
        require(_fee <= 1000, "Max 10%");
        platformFee = _fee;
    }
    
    function withdrawPlatformFees() external onlyOwner {
        uint256 balance = axiToken.balanceOf(address(this));
        // Only withdraw excess (not staked or job payments)
        // Simplified: withdraw all for now
        axiToken.transfer(owner(), balance);
    }
}