// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/**
 * @title AgentRegistry
 * @notice On-chain registry of autonomous agent keys, roles, and status (PRD §4, §8, §12.2).
 * Note: Contract verifies cryptographic key control and authorized role status; it does not verify human identity.
 */
contract AgentRegistry {
    enum AgentRole {
        NONE,
        LEGAL_RESEARCHER,
        LEGAL_INTERPRETER,
        ADVERSARIAL_RESEARCHER,
        EVIDENCE_VERIFIER,
        QUANTITATIVE_FORECASTER,
        COORDINATOR
    }

    struct AgentInfo {
        address walletAddress;
        AgentRole role;
        bytes32 modelVersionHash;
        bool isActive;
        uint256 registeredAt;
        uint256 totalSubmissions;
    }

    address public admin;
    mapping(address => AgentInfo) public agents;
    address[] public registeredAgentList;

    event AgentRegistered(address indexed walletAddress, AgentRole indexed role, bytes32 modelVersionHash, uint256 registeredAt);
    event AgentStatusUpdated(address indexed walletAddress, bool isActive);
    event AgentRoleUpdated(address indexed walletAddress, AgentRole newRole);

    modifier onlyAdmin() {
        require(msg.sender == admin, "AgentRegistry: caller is not admin");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    /**
     * @notice Registers an agent address with a specific analytical role
     */
    function registerAgent(
        address agentAddress,
        AgentRole role,
        bytes32 modelVersionHash
    ) external onlyAdmin {
        require(agentAddress != address(0), "AgentRegistry: invalid address");
        require(role != AgentRole.NONE, "AgentRegistry: role cannot be NONE");
        require(agents[agentAddress].walletAddress == address(0), "AgentRegistry: agent already registered");

        agents[agentAddress] = AgentInfo({
            walletAddress: agentAddress,
            role: role,
            modelVersionHash: modelVersionHash,
            isActive: true,
            registeredAt: block.timestamp,
            totalSubmissions: 0
        });

        registeredAgentList.push(agentAddress);

        emit AgentRegistered(agentAddress, role, modelVersionHash, block.timestamp);
    }

    function setAgentStatus(address agentAddress, bool isActive) external onlyAdmin {
        require(agents[agentAddress].walletAddress != address(0), "AgentRegistry: agent not found");
        agents[agentAddress].isActive = isActive;
        emit AgentStatusUpdated(agentAddress, isActive);
    }

    function setAgentRole(address agentAddress, AgentRole newRole) external onlyAdmin {
        require(agents[agentAddress].walletAddress != address(0), "AgentRegistry: agent not found");
        require(newRole != AgentRole.NONE, "AgentRegistry: invalid role");
        agents[agentAddress].role = newRole;
        emit AgentRoleUpdated(agentAddress, newRole);
    }

    function isAgentActive(address agentAddress) external view returns (bool) {
        return agents[agentAddress].isActive;
    }

    function getAgentRole(address agentAddress) external view returns (AgentRole) {
        return agents[agentAddress].role;
    }

    function getAgentCount() external view returns (uint256) {
        return registeredAgentList.length;
    }
}
