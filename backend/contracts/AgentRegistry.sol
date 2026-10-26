// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentRegistry
 * @dev Manages registered agent roles, statuses, and performance metadata.
 * PRD Section 12.2: "Register agent address, role, and status"
 */
contract AgentRegistry {
    address public admin;

    enum AgentStatus { INACTIVE, ACTIVE, SUSPENDED }

    struct AgentInfo {
        address walletAddress;
        string role;
        string modelVersion;
        AgentStatus status;
        uint256 registeredAt;
    }

    mapping(address => AgentInfo) public agents;
    mapping(address => bool) public isRegistered;

    event AgentRegistered(address indexed agentAddress, string role, string modelVersion);
    event AgentStatusChanged(address indexed agentAddress, AgentStatus status);

    modifier onlyAdmin() {
        require(msg.sender == admin, "AgentRegistry: caller is not admin");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function registerAgent(
        address agentAddress,
        string calldata role,
        string calldata modelVersion
    ) external onlyAdmin {
        require(agentAddress != address(0), "Invalid agent address");
        agents[agentAddress] = AgentInfo({
            walletAddress: agentAddress,
            role: role,
            modelVersion: modelVersion,
            status: AgentStatus.ACTIVE,
            registeredAt: block.timestamp
        });
        isRegistered[agentAddress] = true;

        emit AgentRegistered(agentAddress, role, modelVersion);
    }

    function setAgentStatus(address agentAddress, AgentStatus status) external onlyAdmin {
        require(isRegistered[agentAddress], "Agent not registered");
        agents[agentAddress].status = status;
        emit AgentStatusChanged(agentAddress, status);
    }
}
