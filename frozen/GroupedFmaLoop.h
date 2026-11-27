//===- ExperimentalIndirectLoopPrefetch.h -----------------------*- C++ -*-===//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//===----------------------------------------------------------------------===//
// Course prototype: x86-64 fixed-stride indirect loads only. Training counters
// require a single-threaded, normally terminating run. Training is not timing.
// Selected records are bound to the input SHA256 and checked against branch
// counts. This does not guarantee profitability after workload distribution
// changes. No runtime selection wrapper or arbitrary loop support is implied.
#ifndef LLVM_BOLT_PASSES_EXPERIMENTALINDIRECTLOOPPREFETCH_H
#define LLVM_BOLT_PASSES_EXPERIMENTALINDIRECTLOOPPREFETCH_H
#include "bolt/Passes/BinaryPasses.h"
#include "llvm/MC/MCDisassembler/MCDisassembler.h"
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include "llvm/MC/MCSectionELF.h"
#include "llvm/MC/MCStreamer.h"
class TripCounters final : public llvm::bolt::RuntimeLibrary {
  std::vector<std::string> Names;

public:
  explicit TripCounters(std::vector<std::string> N) : Names(std::move(N)) {}
  void addRuntimeLibSections(std::vector<std::string> &) const override {}
  void
  adjustCommandLineOptions(const llvm::bolt::BinaryContext &) const override {}
  void emitBinary(llvm::bolt::BinaryContext &BC,
                  llvm::MCStreamer &OS) override {
    auto *Sec =
        BC.Ctx->getELFSection(".bolt.tripcounts", llvm::ELF::SHT_PROGBITS,
                              llvm::ELF::SHF_ALLOC | llvm::ELF::SHF_WRITE);
    Sec->setAlignment(llvm::Align(8));
    OS.switchSection(Sec);
    for (auto &Name : Names) {
      auto *Sym = BC.Ctx->getOrCreateSymbol(Name);
      OS.emitSymbolAttribute(Sym, llvm::MCSA_Global);
      OS.emitLabel(Sym);
      for (unsigned K = 0; K < 28; ++K)
        OS.emitIntValue(0, 8);
    }
  }
  void link(llvm::bolt::BinaryContext &, llvm::StringRef,
            llvm::bolt::BOLTLinker &,
            llvm::bolt::BOLTLinker::SectionsMapper) override {}
};

namespace llvm {
namespace bolt {
class IndirectLoopTripTraining : public BinaryFunctionPass {
  std::string Mode;

public:
  explicit IndirectLoopTripTraining(std::string M)
      : BinaryFunctionPass(false), Mode(M) {}
  const char *getName() const override { return "bounded-indirect-loop"; }
  Error runOnFunctions(BinaryContext &BC) override {
    if (Mode != "trip-train")
      return Error::success();
    auto dec = [&](std::initializer_list<uint8_t> X) {
      MCInst I;
      uint64_t N;
      if (BC.DisAsm->getInstruction(I, N,
                                    ArrayRef<uint8_t>(X.begin(), X.size()), 0,
                                    nulls()) != MCDisassembler::Success ||
          N != X.size())
        report_fatal_error("decode");
      return I;
    };
    std::vector<MCInst> Pattern = {dec({0x8b,0x14,0x87}), dec({0xc4,0xc1,0x7b,0x10,0x04,0xc0}), dec({0x48,0x83,0xc0,0x01}), dec({0xc4,0xe2,0xf9,0xb9,0x0c,0xd6}), dec({0x48,0x39,0xc1})};
    unsigned Found = 0;
    std::vector<std::string> Symbols;
    if (!BC.HasFixedLoadAddress || BC.getRuntimeLibrary())
      return Error::success();
    for (auto &[Addr, F] : BC.getBinaryFunctions()) {
      if (!F.isSimple())
        continue;
      auto SafeCFI = [](const MCCFIInstruction &I) {
        switch (I.getOperation()) {
        case MCCFIInstruction::OpDefCfa:
        case MCCFIInstruction::OpDefCfaRegister:
          return I.getRegister() == 7 || I.getRegister() == 6;
        case MCCFIInstruction::OpDefCfaOffset:
        case MCCFIInstruction::OpAdjustCfaOffset:
        case MCCFIInstruction::OpOffset:
        case MCCFIInstruction::OpRestore:
        case MCCFIInstruction::OpRememberState:
        case MCCFIInstruction::OpRestoreState:
        case MCCFIInstruction::OpGnuArgsSize:
          return true;
        default:
          return false;
        }
      };
      bool CanonicalCFI = true;
      for (auto I = F.cie_begin(); I != F.cie_end(); ++I)
        CanonicalCFI &= SafeCFI(*I);
      for (const auto &I : F.getFDEProgram())
        CanonicalCFI &= SafeCFI(I);
      if (!CanonicalCFI)
        continue;

      std::vector<BinaryBasicBlock *> Candidates;
      for (auto &B : F)
        Candidates.push_back(&B);
      for (auto *B : Candidates) {
        if (B->size() != 6 || B->succ_size() != 2)
          continue;
        auto &J = B->getInstructionAtIndex(5);
        if (!BC.MIB->isConditionalBranch(J) || BC.MIB->getCondCode(J) != 5)
          continue;
        auto *Target = BC.MIB->getTargetSymbol(J);
        if (Target != B->getLabel())
          continue;
        bool Self = false;
        for (auto *S : B->successors())
          if (S == B)
            Self = true;
        if (!Self)
          continue;
        std::map<unsigned, unsigned> Map;
        bool Match = true;
        for (unsigned K = 0; Match && K < 5; ++K) {
          auto &R = Pattern[K];
          MCInst A = B->getInstructionAtIndex(K);
          if (K == 4 && A.getOpcode() == R.getOpcode() && A.getNumOperands() == 2 && Map.count(R.getOperand(1).getReg()) && A.getOperand(0).isReg() && A.getOperand(0).getReg() == Map[R.getOperand(1).getReg()])
            std::swap(A.getOperand(0), A.getOperand(1));
          Match = R.getOpcode() == A.getOpcode() &&
                  R.getNumOperands() == A.getNumOperands();
          for (unsigned O = 0; Match && O < R.getNumOperands(); ++O) {
            auto &X = R.getOperand(O);
            auto &Y = A.getOperand(O);
            if (X.isReg() && Y.isReg()) {
              unsigned XR = X.getReg(), YR = Y.getReg();
              if (!XR || !YR) {
                Match = XR == YR;
                continue;
              }
              if (BC.MIB->getRegSize(XR) != BC.MIB->getRegSize(YR)) {
                Match = false;
                break;
              }
              if (Map.count(XR))
                Match = Map[XR] == YR;
              else
                Map[XR] = YR;
            } else
              Match = X.isImm() && Y.isImm() && X.getImm() == Y.getImm();
          }
        }
        if (!Match)
          continue;
        // Pair EDX definition with the RDX index use and reject overlapping
        // roles.
        unsigned Ref32 = Pattern[0].getOperand(0).getReg();
        unsigned Ref64 = BC.MIB->getAliasSized(Ref32, 8);
        if (!Map.count(Ref64) ||
            BC.MIB->getAliasSized(Map[Ref32], 8) != Map[Ref64])
          continue;
        std::map<unsigned, unsigned> Wide;
        for (auto [X, Y] : Map) {
          unsigned WX =
              BC.MIB->getRegSize(X) <= 8 ? BC.MIB->getAliasSized(X, 8) : X;
          unsigned WY =
              BC.MIB->getRegSize(Y) <= 8 ? BC.MIB->getAliasSized(Y, 8) : Y;
          if (Wide.count(WY) && Wide[WY] != WX)
            Match = false;
          Wide[WY] = WX;
        }
        if (!Match)
          continue;
        unsigned SP = dec({0x48, 0x89, 0xe1}).getOperand(1).getReg(),
                 FP = dec({0x48, 0x89, 0xe9}).getOperand(1).getReg();
        for (auto [X, Y] : Map)
          if (BC.MIB->getRegSize(Y) <= 8) {
            unsigned W = BC.MIB->getAliasSized(Y, 8);
            if (W == SP || W == FP)
              Match = false;
          }
        if (!Match)
          continue;
        auto mapped = [&](MCInst I) {
          for (auto &O : I)
            if (O.isReg() && O.getReg()) {
              auto It = Map.find(O.getReg());
              if (It == Map.end())
                report_fatal_error("unmapped loop register");
              O.setReg(It->second);
            }
          return I;
        };

        std::string Name = "__bolt_trip_" + std::to_string(Found);
        Symbols.push_back(Name);
        auto *Counter = BC.Ctx->getOrCreateSymbol(Name);
        std::vector<std::unique_ptr<BinaryBasicBlock>> Blocks;
        for (unsigned K = 0; K < 3; ++K) {
          Blocks.push_back(F.createBasicBlock());
          Blocks.back()->setCFIState(B->getCFIState());
        }
        auto *Body = Blocks[0].get(), *Small = Blocks[1].get(),
             *Long = Blocks[2].get();
        for (auto I : *B) {
          for (auto &O : I)
            if (O.isExpr()) {
              auto *E = dyn_cast<MCSymbolRefExpr>(O.getExpr());
              if (E && &E->getSymbol() == B->getLabel())
                O.setExpr(MCSymbolRefExpr::create(Body->getLabel(), *BC.Ctx));
            }
          Body->addInstruction(I);
        }
        for (auto *Succ : B->successors())
          Body->addSuccessor(Succ == B ? Body : Succ);
        while (B->size())
          B->eraseInstruction(B->begin());
        B->removeAllSuccessors();
        auto emit = [&](BinaryBasicBlock *X,
                        std::initializer_list<uint8_t> Bytes) {
          X->addInstruction(mapped(dec(Bytes)));
        };
        auto count = [&](BinaryBasicBlock *X, unsigned Offset,
                         std::initializer_list<uint8_t> Bytes) {
          MCInst I = dec(Bytes);
          for (auto &O : I)
            if (O.isReg() && Map.count(O.getReg()))
              O.setReg(Map.at(O.getReg()));
          I.getOperand(3) = MCOperand::createExpr(MCBinaryExpr::createAdd(
              MCSymbolRefExpr::create(Counter, *BC.Ctx),
              MCConstantExpr::create(Offset, *BC.Ctx), *BC.Ctx));
          X->addInstruction(I);
        };
        auto branch = [&](BinaryBasicBlock *X, BinaryBasicBlock *Y,
                          int CC = -1) {
          MCInst I;
          if (CC < 0)
            BC.MIB->createUncondBranch(I, Y->getLabel(), BC.Ctx.get());
          else
            BC.MIB->createCondBranch(I, Y->getLabel(), CC, BC.Ctx.get());
          X->addInstruction(I);
          X->addSuccessor(Y);
        };
        emit(B, {0x48, 0x89, 0xca});
        emit(B, {0x48, 0x29, 0xc2});
        
        count(B, 0, {0x48, 0xff, 0x05, 0, 0, 0, 0});
        count(B, 8, {0x48, 0x01, 0x15, 0, 0, 0, 0});
        BinaryBasicBlock *Test = B;
        for (unsigned K = 1; K <= 16; ++K) {
          Blocks.push_back(F.createBasicBlock());
          auto *Hit = Blocks.back().get();
          Hit->setCFIState(B->getCFIState());
          Blocks.push_back(F.createBasicBlock());
          auto *Next = Blocks.back().get();
          Next->setCFIState(B->getCFIState());
          MCInst C = mapped(dec({0x48, 0x83, 0xfa, 0x01}));
          C.getOperand(C.getNumOperands() - 1).setImm(K);
          Test->addInstruction(C);
          branch(Test, Hit, 4);
          branch(Test, Next);
          count(Hit, (K<=4?48+(K-1)*8:96+(K-5)*8), {0x48, 0xff, 0x05, 0, 0, 0, 0});
          branch(Hit, Small);
          Test = Next;
        }

        emit(Test, {0x48,0x81,0xfa,0x10,0x0,0x0,0x0});
        branch(Test,Small,6);branch(Test,Long);
        count(Small,24,{0x48,0x01,0x15,0,0,0,0});branch(Small,Body);
        count(Long,32,{0x48,0xff,0x05,0,0,0,0});
        emit(Long,{0x48,0x81,0xea,0x1,0x0,0x0,0x0});emit(Long,{0x48,0x81,0xe2,0xfc,0xff,0xff,0xff});
        count(Long,16,{0x48,0x01,0x15,0,0,0,0});
        emit(Long,{0x48,0x89,0xca});emit(Long,{0x48,0x29,0xc2});
        emit(Long,{0x48,0x83,0xea,1});emit(Long,{0x48,0x81,0xe2,0x3,0x0,0x0,0x0});emit(Long,{0x48,0x81,0xc2,0x1,0x0,0x0,0x0});
        count(Long,24,{0x48,0x01,0x15,0,0,0,0});
        auto *TailTest = Long;
        for (unsigned K=1; K<=4; ++K) {
          Blocks.push_back(F.createBasicBlock()); auto *Hit=Blocks.back().get(); Hit->setCFIState(B->getCFIState());
          Blocks.push_back(F.createBasicBlock()); auto *Next=Blocks.back().get(); Next->setCFIState(B->getCFIState());
          auto C=mapped(dec({0x48,0x83,0xfa,0x01})); C.getOperand(C.getNumOperands()-1).setImm(K); TailTest->addInstruction(C);
          branch(TailTest,Hit,4); branch(TailTest,Next);
          count(Hit,192+(K-1)*8,{0x48,0xff,0x05,0,0,0,0}); branch(Hit,Body); TailTest=Next;
        }
        branch(TailTest,Body);
        BC.outs() << "TRIP-TRAIN " << Name << " function " << F.getPrintName()
                  << " offset " << B->getOffset() << "\n";
        F.insertBasicBlocks(B, std::move(Blocks));
        F.clearProfile();
        ++Found;
      }
    }
    if (Found)
      BC.setRuntimeLibrary(std::make_unique<TripCounters>(std::move(Symbols)));
    return Error::success();
  }
};
} // namespace bolt
} // namespace llvm

#include "bolt/Passes/BinaryPasses.h"
#include "llvm/ADT/StringExtras.h"
#include "llvm/MC/MCDisassembler/MCDisassembler.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SHA256.h"
#include <map>
namespace llvm {
namespace bolt {
class IndirectLoopPrefetch : public BinaryFunctionPass {
  std::string Mode, Profile;
  bool PeelTail;

public:
  explicit IndirectLoopPrefetch(std::string M, std::string P, bool Peel = false)
      : BinaryFunctionPass(false), Mode(M), Profile(P), PeelTail(Peel) {}
  const char *getName() const override { return "bounded-indirect-loop"; }
  Error runOnFunctions(BinaryContext &BC) override {
    if (Mode != "selected")
      return Error::success();
    if (Profile.empty())
      return Error::success();
    auto Buffer = MemoryBuffer::getFile(Profile);
    if (!Buffer)
      report_fatal_error("cannot read trip profile");
    auto Parsed = json::parse((*Buffer)->getBuffer());
    if (!Parsed)
      report_fatal_error("invalid trip JSON");
    auto *Root = Parsed->getAsObject();
    if (!Root ||
        Root->getString("schema").value_or("") != "bolt-group-u4-d0-m16-h2-v1" ||
        Root->getInteger("distance").value_or(-1) != 0 ||
        Root->getInteger("unroll").value_or(0) != 4)
      report_fatal_error("unsupported trip profile schema");
    auto Input = MemoryBuffer::getFile(BC.getFilename());
    if (!Input)
      report_fatal_error("cannot read input for trip binding");
    auto Bytes = (*Input)->getBuffer();
    auto Hash = SHA256::hash(
        ArrayRef<uint8_t>((const uint8_t *)Bytes.data(), Bytes.size()));
    if (Root->getString("source_sha256").value_or("") !=
        toHex(ArrayRef<uint8_t>(Hash), true))
      report_fatal_error("trip profile input mismatch");
    auto *Records = Root->getArray("loops");
    if (!Records)
      report_fatal_error("missing trip loops");
    std::set<std::pair<std::string, int64_t>> Keys;
    unsigned Requested = 0;
    for (auto &V : *Records) {
      auto *R = V.getAsObject();
      if (!R)
        report_fatal_error("invalid trip record");
      auto Name = R->getString("function");
      auto Offset = R->getInteger("offset");
      if (!Name || !Offset || *Offset < 0 ||
          !Keys.emplace(Name->str(), *Offset).second)
        report_fatal_error("duplicate or malformed trip identity");
      if (R->getBoolean("selected").value_or(false))
        ++Requested;
    }

    auto dec = [&](std::initializer_list<uint8_t> X) {
      MCInst I;
      uint64_t N;
      if (BC.DisAsm->getInstruction(I, N,
                                    ArrayRef<uint8_t>(X.begin(), X.size()), 0,
                                    nulls()) != MCDisassembler::Success ||
          N != X.size())
        report_fatal_error("decode");
      return I;
    };
    std::vector<MCInst> Pattern = {dec({0x8b,0x14,0x87}), dec({0xc4,0xc1,0x7b,0x10,0x04,0xc0}), dec({0x48,0x83,0xc0,0x01}), dec({0xc4,0xe2,0xf9,0xb9,0x0c,0xd6}), dec({0x48,0x39,0xc1})};
    unsigned Found = 0;
    for (auto &[Addr, F] : BC.getBinaryFunctions()) {
      if (!F.isSimple())
        continue;
      auto SafeCFI = [](const MCCFIInstruction &I) {
        switch (I.getOperation()) {
        case MCCFIInstruction::OpDefCfa:
        case MCCFIInstruction::OpDefCfaRegister:
          return I.getRegister() == 7 || I.getRegister() == 6;
        case MCCFIInstruction::OpDefCfaOffset:
        case MCCFIInstruction::OpAdjustCfaOffset:
        case MCCFIInstruction::OpOffset:
        case MCCFIInstruction::OpRestore:
        case MCCFIInstruction::OpRememberState:
        case MCCFIInstruction::OpRestoreState:
        case MCCFIInstruction::OpGnuArgsSize:
          return true;
        default:
          return false;
        }
      };
      bool CanonicalCFI = true;
      for (auto I = F.cie_begin(); I != F.cie_end(); ++I)
        CanonicalCFI &= SafeCFI(*I);
      for (const auto &I : F.getFDEProgram())
        CanonicalCFI &= SafeCFI(I);
      if (!CanonicalCFI)
        continue;

      std::vector<BinaryBasicBlock *> Candidates;
      for (auto &B : F)
        Candidates.push_back(&B);
      for (auto *B : Candidates) {
        if (B->size() != 6 || B->succ_size() != 2)
          continue;
        auto &J = B->getInstructionAtIndex(5);
        if (!BC.MIB->isConditionalBranch(J) || BC.MIB->getCondCode(J) != 5)
          continue;
        auto *Target = BC.MIB->getTargetSymbol(J);
        if (Target != B->getLabel())
          continue;
        bool Self = false;
        for (auto *S : B->successors())
          if (S == B)
            Self = true;
        if (!Self)
          continue;
        std::map<unsigned, unsigned> Map;
        bool Match = true;
        for (unsigned K = 0; Match && K < 5; ++K) {
          auto &R = Pattern[K];
          MCInst A = B->getInstructionAtIndex(K);
          if (K == 4 && A.getOpcode() == R.getOpcode() && A.getNumOperands() == 2 && Map.count(R.getOperand(1).getReg()) && A.getOperand(0).isReg() && A.getOperand(0).getReg() == Map[R.getOperand(1).getReg()])
            std::swap(A.getOperand(0), A.getOperand(1));
          Match = R.getOpcode() == A.getOpcode() &&
                  R.getNumOperands() == A.getNumOperands();
          for (unsigned O = 0; Match && O < R.getNumOperands(); ++O) {
            auto &X = R.getOperand(O);
            auto &Y = A.getOperand(O);
            if (X.isReg() && Y.isReg()) {
              unsigned XR = X.getReg(), YR = Y.getReg();
              if (!XR || !YR) {
                Match = XR == YR;
                continue;
              }
              if (BC.MIB->getRegSize(XR) != BC.MIB->getRegSize(YR)) {
                Match = false;
                break;
              }
              if (Map.count(XR))
                Match = Map[XR] == YR;
              else
                Map[XR] = YR;
            } else
              Match = X.isImm() && Y.isImm() && X.getImm() == Y.getImm();
          }
        }
        if (!Match)
          continue;
        // Pair EDX definition with the RDX index use and reject overlapping
        // roles.
        unsigned Ref32 = Pattern[0].getOperand(0).getReg();
        unsigned Ref64 = BC.MIB->getAliasSized(Ref32, 8);
        if (!Map.count(Ref64) ||
            BC.MIB->getAliasSized(Map[Ref32], 8) != Map[Ref64])
          continue;
        std::map<unsigned, unsigned> Wide;
        for (auto [X, Y] : Map) {
          unsigned WX =
              BC.MIB->getRegSize(X) <= 8 ? BC.MIB->getAliasSized(X, 8) : X;
          unsigned WY =
              BC.MIB->getRegSize(Y) <= 8 ? BC.MIB->getAliasSized(Y, 8) : Y;
          if (Wide.count(WY) && Wide[WY] != WX)
            Match = false;
          Wide[WY] = WX;
        }
        if (!Match)
          continue;
        unsigned SP = dec({0x48, 0x89, 0xe1}).getOperand(1).getReg(),
                 FP = dec({0x48, 0x89, 0xe9}).getOperand(1).getReg();
        for (auto [X, Y] : Map)
          if (BC.MIB->getRegSize(Y) <= 8) {
            unsigned W = BC.MIB->getAliasSized(Y, 8);
            if (W == SP || W == FP)
              Match = false;
          }
        if (!Match)
          continue;

        const json::Object *Record = nullptr;
        for (auto &V : *Records) {
          auto *R = V.getAsObject();
          if (!R)
            report_fatal_error("invalid loop record");
          if (R->getString("function").value_or("") == F.getPrintName() &&
              R->getInteger("offset").value_or(-1) == (int64_t)B->getOffset()) {
            if (Record)
              report_fatal_error("duplicate loop record");
            Record = R;
          }
        }
        if (!Record || !Record->getBoolean("selected").value_or(false))
          continue;
        auto *Counts = Record->getObject("counts");
        if (!Counts)
          report_fatal_error("missing trip counts");
        auto Read = [&](StringRef Key) -> uint64_t {
          auto N = Counts->getInteger(Key);
          if (!N || *N < 0)
            report_fatal_error("invalid trip counter");
          return *N;
        };
        uint64_t NL=Read("local_low"),NH=Read("local_high");
        uint64_t N = Read("entries"), I = Read("iterations"),
                 P = Read("prefetch_iterations"), T = Read("plain_iterations"),
                 L = Read("eligible_entries"), O = Read("odd_long_entries");
        if (P > I || T != I - P || L > N || O > N - L || T < N || P % 4 ||
            P / 4 < L || N == 0)
          report_fatal_error("inconsistent trip counters");
        uint64_t H[4]={0,0,0,0}, TailI=0;
        if (PeelTail) {
          uint64_t Sum=0;
          for(unsigned K=0;K<4;++K) { H[K]=Read("long_tail_"+std::to_string(K+1)); if(H[K]>L-Sum || H[K]>(T-TailI)/(K+1)) report_fatal_error("invalid tail histogram"); Sum+=H[K]; TailI+=(K+1)*H[K]; }
          if(Sum!=L || TailI>T || T-TailI<N-L) report_fatal_error("inconsistent tail histogram");
        }
        if (!B->hasProfile() || B->getExecutionCount() != I)
          report_fatal_error("trip and branch profiles disagree");
        uint64_t Exits = 0;
        for (auto *Succ : B->successors())
          if (Succ != B)
            Exits += B->getBranchInfo(*Succ).Count;
        if (Exits != N)
          report_fatal_error("trip exit count mismatch");
        auto mapped = [&](MCInst I) {
          for (auto &O : I)
            if (O.isReg() && O.getReg()) {
              auto It = Map.find(O.getReg());
              if (It == Map.end())
                report_fatal_error("unmapped loop register");
              O.setReg(It->second);
            }
          return I;
        };

        std::vector<MCInst> Original(B->begin(), B->end());
        BinaryBasicBlock *Exit=nullptr;
        for(auto *S:B->successors()) if(S!=B) Exit=S;
        if(!Exit) report_fatal_error("missing original exit");
        std::vector<std::unique_ptr<BinaryBasicBlock>> Blocks;
        auto make=[&](){Blocks.push_back(F.createBasicBlock());auto *X=Blocks.back().get();X->setCFIState(B->getCFIState());return X;};
        auto *Plain=make(), *Body=make();
        BinaryBasicBlock *Tail[4]={nullptr,nullptr,nullptr,nullptr};
        if(PeelTail) for(auto &X:Tail) X=make();
        Plain->setAlignment(16);Plain->setAlignmentMaxBytes(15);
        Body->setAlignment(16);Body->setAlignmentMaxBytes(15);
        for(auto Inst:Original){
          for(auto &Op:Inst) if(Op.isExpr()){
            auto *Expr=dyn_cast<MCSymbolRefExpr>(Op.getExpr());
            if(Expr && &Expr->getSymbol()==B->getLabel()) Op.setExpr(MCSymbolRefExpr::create(Plain->getLabel(),*BC.Ctx));
          }
          Plain->addInstruction(Inst);
        }
        Plain->addSuccessor(Plain);Plain->addSuccessor(Exit);
        auto emit=[&](BinaryBasicBlock *X,std::initializer_list<uint8_t> Bytes){X->addInstruction(mapped(dec(Bytes)));};
        auto branch=[&](BinaryBasicBlock *X,BinaryBasicBlock *Y,int CC=-1){MCInst Inst;if(CC<0)BC.MIB->createUncondBranch(Inst,Y->getLabel(),BC.Ctx.get());else BC.MIB->createCondBranch(Inst,Y->getLabel(),CC,BC.Ctx.get());X->addInstruction(Inst);X->addSuccessor(Y);};
        while(B->size())B->eraseInstruction(B->begin());B->removeAllSuccessors();
        emit(B,{0x48,0x89,0xca});emit(B,{0x48,0x29,0xc2});emit(B,{0x48,0x81,0xfa,0x10,0x0,0x0,0x0});
        branch(B,Plain,6);branch(B,Body);
        for(unsigned K=0;K<4;++K){
          
          for(unsigned J=0;J<4;++J)Body->addInstruction(Original[J]);
        }
        // Keep 1..U original iterations (or D+1..D+U for prefetch).
        // Never alter the original end register, and never reassociate FMA.
        emit(Body,{0x48,0x89,0xca});emit(Body,{0x48,0x29,0xc2});emit(Body,{0x48,0x81,0xfa,0x4,0x0,0x0,0x0});
        branch(Body,Body,7);branch(Body,PeelTail ? Tail[0] : Plain);
        if(PeelTail) for(unsigned K=0;K<4;++K) {
          for(unsigned J=0;J<5;++J) Tail[K]->addInstruction(Original[J]);
          if(K<3) { branch(Tail[K],Exit,4); branch(Tail[K],Tail[K+1]); }
          else branch(Tail[K],Exit);
        }
        B->setExecutionCount(N);Body->setExecutionCount(P/4);Plain->setExecutionCount(T);
        auto edge=[&](BinaryBasicBlock *X,BinaryBasicBlock *Y,uint64_t Count){X->getBranchInfo(*Y).Count=Count;X->getBranchInfo(*Y).MispredictedCount=0;};
        edge(B,Plain,N-L);edge(B,Body,L);edge(Body,Body,P/4-L);
        if(PeelTail) {
          edge(Body,Tail[0],L); Plain->setExecutionCount(T-TailI);
          edge(Plain,Plain,T-TailI-(N-L));edge(Plain,Exit,N-L);
          uint64_t Left=L;
          for(unsigned K=0;K<4;++K) { Tail[K]->setExecutionCount(Left); edge(Tail[K],Exit,H[K]); Left-=H[K]; if(K<3) edge(Tail[K],Tail[K+1],Left); }
        } else {edge(Body,Plain,L);edge(Plain,Plain,T-N);edge(Plain,Exit,N);}
        F.insertBasicBlocks(B,std::move(Blocks));
        BC.outs() << "TRIP-SELECT applied " << F.getPrintName() << " entries "
                  << N << " iterations " << I << "\n";
        ++Found;
        BC.outs() << "LOOP-PREFETCH transformed " << F.getPrintName() << "\n";
      }
    }
    if (Found != Requested)
      report_fatal_error("selected loop not recognized");
    BC.outs() << "LOOP-PREFETCH loops " << Found << "\n";
    return Error::success();
  }
};
} // namespace bolt
} // namespace llvm

#endif
